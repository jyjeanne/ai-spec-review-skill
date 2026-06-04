# Frontend Performance Review Heuristics

## Focus areas

- **Core Web Vitals**: LCP, INP, CLS — definitions, thresholds, debugging sub-parts
- **Bundle optimization**: code splitting, tree shaking, dynamic imports, bundle budgets
- **Image strategy**: responsive images, modern formats, lazy loading, CDN
- **Font strategy**: font-display, subsetting, self-hosting, preloading
- **Rendering performance**: virtual DOM, layout thrashing, Web Workers
- **Caching**: service workers, Cache API, HTTP caching headers

---

## Core Web Vitals

### LCP — Largest Contentful Paint (< 2.5s)

Measures when the largest visible content element (hero image, heading, text block)
becomes visible to the user. This is the perceived load speed.

**LCP sub-parts (diagnose which phase is slow):**

| Phase | What it measures | Common issues |
|-------|-----------------|---------------|
| TTFB | Time to first byte — server response | Slow server, no CDN, unoptimized database queries |
| Resource load delay | Time before browser starts loading the LCP resource | LCP resource not discoverable early (injected by JS, lazy-loaded, requires CSS background-image) |
| Resource load duration | Network time for the resource | Large unoptimized image, no CDN, no compression |
| Element render delay | Time from resource load to rendering | Render-blocking resources (JS, CSS), client-side rendering waterfall |

**Critical rules:**
- The LCP element (usually a hero image or heading) must be in the initial HTML —
  never injected by JavaScript
- Never `loading="lazy"` on the LCP image
- Preload the LCP image: `<link rel="preload" as="image" href="hero.webp">`

### INP — Interaction to Next Paint (< 200ms)

Measures responsiveness: the time from a user interaction (click, tap, key press) to
the next visual update. Replaced FID in March 2024.

**INP sub-parts:**

| Phase | What it measures |
|-------|-----------------|
| Input delay | Time from interaction to event handler starting (blocked by long tasks) |
| Processing time | Time spent in event handlers |
| Presentation delay | Time from handler completion to visual update (layout, paint) |

**Causes of high INP:**
- Long tasks (>50ms) on the main thread — break them up with `setTimeout` or `scheduler.yield()`
- Expensive event handlers — offload to Web Workers
- Large DOM sizes (>1500 nodes) causing slow style recalculation
- Synchronous layout operations (reading then writing DOM properties in sequence)

### CLS — Cumulative Layout Shift (< 0.1)

Measures visual stability: how much content shifts during page load.

**Common causes:**
- Images without `width`/`height` attributes — browser doesn't reserve space
- Dynamically injected content (ads, banners, cookie notices) pushing content down
- Web fonts causing FOUT (Flash of Unstyled Text) with layout shift
- Animations that change layout properties (use `transform` instead of `width`/`top`)

**Fix patterns:**
- Always set explicit `width` and `height` on images and video elements
- Reserve space for dynamic content with `min-height` or skeleton placeholders
- Use `font-display: optional` or `swap` combined with size-adjust for web fonts
- Animate with `transform` and `opacity` only (compositor-only properties)

---

## Bundle Optimization

### Code splitting

- **Route-based splitting**: `React.lazy()` / `Next.js dynamic import` / `defineAsyncComponent`
  (Vue) — only load code for the current route
- **Component-based splitting**: lazy-load below-the-fold components: modals, drawers,
  chart libraries, rich text editors, video players
- **Vendor splitting**: separate framework code (React, Vue) from application code —
  framework changes infrequently, app code changes frequently. Framework bundle stays cached

### Tree shaking

- Use ES module imports (`import { X } from 'lib'`) not CommonJS (`const { X } = require('lib')`)
- Avoid side effects in module top-level scope (bundlers can't tree-shake modules with side effects)
- Use `sideEffects: false` in `package.json` if the package has no side-effectful modules
- Use production builds (`NODE_ENV=production`) which enable dead-code elimination

### Dynamic imports

```javascript
// Before: always loaded
import heavyChart from 'heavy-chart-library';

// After: loaded on demand (returns a promise)
const heavyChart = await import('heavy-chart-library');
// or with React
const HeavyChart = React.lazy(() => import('heavy-chart-library'));
```

### Bundle analysis

- **webpack-bundle-analyzer**: visualize bundle composition, find large dependencies
- **source-map-explorer**: similar, works with any bundler's source maps
- **rollup-plugin-visualizer**: for Rollup/Vite projects
- **Bundlephobia**: check npm package sizes before adding dependencies (`bundlephobia.com`)

### Bundle budgets

Set CI-enforced limits. Example:

```json
{
  "budgets": [{
    "type": "initial",
    "maximumWarning": "200KB",
    "maximumError": "300KB"
  }]
}
```

---

## Image Strategy

### Responsive images

```html
<img
  src="photo-800w.jpg"
  srcset="photo-400w.jpg 400w, photo-800w.jpg 800w, photo-1200w.jpg 1200w"
  sizes="(max-width: 600px) 400px, (max-width: 1200px) 800px, 1200px"
  alt="..."
  width="1200"
  height="800"
/>
```

The browser selects the right resolution based on viewport size and device pixel ratio.

### Modern formats

| Format | Compression vs JPEG | Browser support |
|--------|-------------------|-----------------|
| WebP | 25-35% smaller | Universal |
| AVIF | 50% smaller, better quality | Chrome, Firefox, Safari 16.4+ |

```html
<picture>
  <source srcset="photo.avif" type="image/avif">
  <source srcset="photo.webp" type="image/webp">
  <img src="photo.jpg" alt="..." width="800" height="600">
</picture>
```

### Lazy loading

- **Native**: `<img loading="lazy">` — browser handles it. Do NOT use on the LCP image
- **Intersection Observer**: for more control (background images, iframes, complex components)
- **LQIP (Low Quality Image Placeholder)**: serve a tiny blurred placeholder immediately,
  replace with full image when loaded

### Image CDN

Services (Cloudinary, imgix, Cloudflare Images) that:
- Resize images on the fly based on URL parameters
- Convert to optimal format based on browser
- Compress without visible quality loss
- Cache at edge locations worldwide

---

## Font Strategy

### font-display

| Value | Behavior | Best for |
|-------|----------|----------|
| `swap` | Show fallback text immediately, swap to custom font when loaded | Most cases — prevents invisible text |
| `block` | Hide text for up to 3s waiting for font, then fallback | Brand-critical fonts |
| `fallback` | Hide text for ~100ms, then fallback; short swap window | Content where font matters but FOUT is OK |
| `optional` | Hide text for ~100ms, then fallback; no swap | Performance-critical; font is enhancement only |

Recommendation: `font-display: swap` for most content fonts. Be aware of layout shift
when the font swaps — mitigate with `size-adjust`:

```css
@font-face {
  font-family: 'Custom';
  src: url('custom.woff2');
  font-display: swap;
  size-adjust: 105%; /* match fallback font metrics */
}
```

### Subsetting

If you only use Latin characters, don't serve the full font with CJK glyphs. Subset
to the characters you need. Tools: `glyphhanger`, `fonttools pyftsubset`.

### Self-hosting

Self-host fonts instead of using Google Fonts CDN:
- Fewer DNS lookups and TLS handshakes
- Better caching control
- No dependency on third-party availability

### Preloading

```html
<link rel="preload" as="font" href="custom.woff2" type="font/woff2" crossorigin>
```

Only preload fonts used above the fold. Preloading too many fonts wastes bandwidth
and delays other resources.

---

## Rendering Performance

### Layout thrashing

**Problem:** Reading a layout property (offsetHeight, getBoundingClientRect) forces
the browser to compute layout. If you then modify the DOM and read again, you force
layout twice in one frame.

**Fix:** Batch reads, then batch writes. Never interleave reads and writes in a loop.

```javascript
// Bad: read-write-read-write in a loop (layout thrashing)
elements.forEach(el => {
  const height = el.offsetHeight; // read forces layout
  el.style.height = height * 2 + 'px'; // write invalidates layout
});

// Good: batch all reads, then batch all writes
const heights = elements.map(el => el.offsetHeight); // reads
elements.forEach((el, i) => el.style.height = heights[i] * 2 + 'px'); // writes
```

### Web Workers

Offload CPU-heavy work from the main thread:
- JSON parsing of large payloads (>100KB)
- Encryption/decryption
- Image manipulation (resize, format conversion)
- Data sorting/filtering/transformation on large arrays

```javascript
const worker = new Worker('data-processor.js');
worker.postMessage({ data: largeDataset });
worker.onmessage = (e) => updateUI(e.data.result);
```

### Virtual scrolling

For lists with 100+ items, render only visible items. Libraries: `react-window`,
`vue-virtual-scroller`, `@tanstack/virtual`.

### React-specific rendering optimizations

- **`React.memo`**: skip re-render when props haven't changed
- **`useMemo` / `useCallback`**: stabilize derived values and callbacks to prevent
  unnecessary child re-renders
- **Avoid inline objects/arrays as props**: `style={{ color: 'red' }}` creates a new
  object every render → child always re-renders. Extract to constant outside component
- **Lift content state, not UI state**: don't store derived state
- **React Compiler** (React 19+): auto-memoizes components — may reduce need for manual
  memoization

---

## Caching (Frontend)

### Service Workers

Enable offline support and instant subsequent loads. Cache the application shell
(HTML, CSS, JS) on install. Cache API responses at runtime.

**Cache strategies:**

| Strategy | Pattern | Use case |
|----------|---------|----------|
| Cache-first | Return cached; if not cached, fetch and cache | Static assets (CSS, JS, fonts, images) |
| Network-first | Fetch; if fails, return cached | API responses that should be fresh |
| Stale-while-revalidate | Return cached immediately; fetch in background to update cache | User profile, settings — need speed but want freshness |

### HTTP caching

```
Cache-Control: public, max-age=31536000, immutable
```

- `public`: can be cached by browser and CDN
- `max-age`: how long (in seconds) the response is fresh
- `immutable`: resource will never change (use for versioned assets: `app.a1b2c3d.js`)

For unversioned URLs that may change (`index.html`):
```
Cache-Control: no-cache  # always validate before using cached copy
```

---

## Common Risks

- LCP resource loaded via JavaScript or CSS `background-image` — not discoverable early
- Render-blocking JavaScript in `<head>` — add `async` or `defer`
- No `width`/`height` on images causing CLS
- Entire application JS (including admin-only features) loaded on every page
- Third-party scripts (analytics, chat widgets, ads) blocking the main thread
- Web font causing invisible text or layout shift (`font-display` not set)
- No image optimization pipeline — serving 3000px photos in 300px containers
- No service worker or HTTP caching strategy

## Review questions

- What is the LCP element for each page? Is it in the initial HTML?
- Are critical images preloaded and not lazy-loaded?
- Is there a bundle budget enforced in CI? What is the current main bundle size?
- Is code splitting implemented? Are below-the-fold components lazy-loaded?
- Do all images have explicit `width` and `height` attributes?
- Is `font-display` set on all `@font-face` declarations?
- Are third-party scripts loaded with `async` or `defer` to avoid blocking?
- Is there a service worker strategy defined? Which cache strategy for each asset type?
- Are long tasks (>50ms) on the main thread identified and broken up?
