# Performance Review Heuristics

## Focus areas

- **Profiling methodology**: measurement before optimization
- **Database performance**: indexes, query optimization, connection pooling, ORM pitfalls
- **Frontend performance**: Core Web Vitals, bundle size, rendering
- **Caching strategy**: patterns, invalidation, tradeoffs
- **Async I/O and concurrency**: event loop, thread pools, backpressure
- **Serverless and cold starts**: optimization strategies
- **Performance measurement**: percentiles, histograms, SLO-based alerting
- **Anti-patterns**: common performance mistakes in specs and implementations

---

## Profiling Methodology

### Golden rule: measure before optimizing

Without profiling, "optimizations" are guesses. Every performance decision must be grounded
in measurement of real or simulated workloads.

### Instrumentation by layer

| Layer | What to measure | Tooling |
|-------|----------------|---------|
| Frontend | LCP, INP, CLS, JS execution time | Lighthouse, Web Vitals API, Chrome DevTools Performance tab |
| API / backend | Request latency (p50/p95/p99), error rate, throughput | OpenTelemetry, Prometheus, Datadog APM |
| Database | Query duration, locks, connection wait time | pg_stat_statements, MySQL slow query log, query plan analysis |
| Infrastructure | CPU, memory, disk I/O, network | Prometheus node_exporter, CloudWatch, Grafana agent |

### Profiling workflow

1. Define performance acceptance criteria (e.g., "p95 API latency < 200ms")
2. Instrument the system with metrics collection
3. Load test at expected and peak concurrency
4. Identify the slowest 5% of operations (p95+)
5. Profile those operations to find the bottleneck (CPU, I/O, lock contention, network)
6. Fix the bottleneck, re-measure, repeat

### Language-specific profilers

| Language | Profiler | Notes |
|----------|---------|-------|
| Python | cProfile + snakeviz, py-spy | py-spy for production profiling without code changes |
| Node.js | Clinic.js, 0x (flame graphs), --inspect + Chrome DevTools | CPU profiling, heap snapshots, async stack traces |
| Java | JProfiler, async-profiler, JDK Flight Recorder | Low-overhead production profiling |
| Go | pprof (net/http/pprof) | Built-in; CPU, heap, goroutine, block, mutex profiles |
| Ruby | stackprof, rbspy | rbspy for production profiling |
| Rust | perf + flamegraph-rs, criterion (benchmarks) | System-level profiling with perf |
| C# | dotTrace, PerfView, dotnet-counters | Built-in EventPipe diagnostics |

---

## Database Performance

### Index strategy

- **Covering indexes**: include all columns needed by a query so the index alone satisfies it
  — avoids table lookups entirely
- **Composite index column order**: put equality-filtered columns first, then range-filtered
  columns, then included columns. The index is only usable for the leftmost prefix of columns
- **Partial indexes**: index only rows matching a condition (`WHERE status = 'active'`) —
  smaller index, faster writes, ideal for filtering on a common condition
- **Index-only scans**: the query selects only columns that exist in the index —
  the database never touches the table
- **Unused index detection**: query `pg_stat_user_indexes` or `sys.dm_db_index_usage_stats`
  to find indexes that are never scanned but still incur write overhead

### Query optimization

- **EXPLAIN / EXPLAIN ANALYZE**: always review query plans. Key indicators:
  - `Seq Scan` on a large table where an index should be used
  - `Nested Loop` where a hash or merge join would be faster
  - High `rows` estimate vs actual — indicates stale statistics (`ANALYZE` needed)
- **Join algorithms**:
  - Nested loop: good when one side is small (inner side indexed)
  - Hash join: good for medium-large unsorted sets
  - Merge join: good when both sides are pre-sorted
- **Common anti-patterns**:
  - `SELECT *` — fetches unnecessary columns, prevents index-only scans
  - Missing `LIMIT` on potentially large result sets
  - Function calls on indexed columns in `WHERE` (`WHERE LOWER(name) = 'foo'` instead of
    functional index or normalized column)
  - `SELECT ... FOR UPDATE` with joins — locks more rows than intended

### Connection pooling

- **Pool sizing formula**: `pool_size = (core_count * 2) + effective_spindle_count`
  is a starting point, but measure actual wait times under load
- **Too-small pool**: threads block waiting for connections → latency spikes under load
- **Too-large pool**: database CPU contention from too many active connections →
  throughput drops. PostgreSQL typically peaks at ~100-200 active connections (depends on query patterns and hardware)
- **Pooler tools**: PgBouncer (transaction pooling mode), Pgpool-II, RDS Proxy
- **Connection timeout**: set a connection acquisition timeout (e.g., 30s) so callers
  fail fast rather than queuing indefinitely

### Schema design for performance

- **Normalization**: reduces data duplication, improves write performance, simplifies updates
- **Denormalization**: pre-compute joins for read-heavy workloads. Accept write overhead
  and potential inconsistency. Use materialized views for declarative denormalization
- **Partitioning**: split large tables by range (date), list (region), or hash.
  Improves query performance via partition pruning and simplifies data archival
- **Materialized views**: pre-computed query results refreshed on schedule. Use for
  expensive aggregations that don't need real-time freshness

### ORM performance anti-patterns

| Anti-pattern | What happens | Fix |
|-------------|--------------|-----|
| **N+1 queries** | Loading a list of objects, then iterating to load each object's relations — one additional query per object | Eager loading: `select_related` (JOIN) or `prefetch_related` (separate query + in-memory join) |
| **Lazy loading in loops** | ORM fetches related objects on attribute access inside a loop | Disable lazy loading for the query; use eager loading explicitly |
| **No `select_related` for FK access** | Separate query for each foreign key access | `select_related('author', 'category')` |
| **Mass updates via ORM objects** | Load 10,000 objects to change one field | Use `.update()` on queryset level: `Model.objects.filter(...).update(field=value)` |
| **Missing `.only()` or `.defer()`** | Fetching all columns when only 2 are needed | Use `.only('id', 'name')` or `.defer('large_text_field')` |
| **Count via `.count()` after filtering** | `len(queryset)` fetches all objects; `.count()` does `SELECT COUNT(*)` | Always use `.count()` for counting |

---

## Frontend Performance

### Core Web Vitals

| Metric | Threshold (good) | What it measures |
|--------|-----------------|------------------|
| **LCP** (Largest Contentful Paint) | < 2.5s | When the largest content element becomes visible. Measures perceived load speed |
| **INP** (Interaction to Next Paint) | < 200ms | Responsiveness to user interactions (clicks, taps, key presses). Replaced FID in March 2024 |
| **CLS** (Cumulative Layout Shift) | < 0.1 | Visual stability — how much the page layout shifts during loading |

LCP sub-parts to debug:
- **TTFB** (Time to First Byte): server response time, redirects, DNS
- **Resource load delay**: time before the browser starts loading the LCP resource
  (affected by `loading="lazy"` on LCP image, render-blocking JS/CSS)
- **Resource load duration**: network time for the resource itself
- **Element render delay**: time from resource load to actual rendering

### Bundle size and code splitting

- **Bundle budget**: set CI-enforced limits (e.g., "initial JS bundle < 200KB gzipped")
- **Route-based splitting**: `React.lazy()` / `Next.js dynamic import` — only load code
  for the current route
- **Component-based splitting**: lazy-load below-the-fold components, modals,
  chart libraries, rich text editors
- **Tree shaking**: ensure bundler is configured for dead code elimination.
  Use ES module imports (not `require()`) and avoid side effects in module scope
- **Dynamic imports**: `import('heavy-library')` returns a promise — load on demand
- **Bundle analysis**: use `webpack-bundle-analyzer`, `source-map-explorer`,
  or `rollup-plugin-visualizer` to find large dependencies

### Image optimization

- **Responsive images**: `srcset` + `sizes` attribute to serve appropriate resolution
  per viewport. Never serve a 2000px image in a 400px container
- **Modern formats**: WebP (27% smaller than PNG), AVIF (50% smaller than JPEG).
  Use `<picture>` with multiple `<source>` elements for fallback
- **Lazy loading**: `loading="lazy"` on images below the fold (note: do NOT lazy-load
  the LCP image — it will delay LCP)
- **Image CDN**: services like imgix, Cloudinary, or Cloudflare Images handle resizing,
  format conversion, and caching automatically

### Font optimization

- **`font-display: swap`**: show fallback text immediately, swap to custom font when loaded
  (prevents FOIT — Flash of Invisible Text)
- **Subset fonts**: only include characters/glyphs the app actually uses
- **Self-host fonts**: avoid third-party font CDNs (extra DNS lookup, connection negotiation)
- **`preload` critical fonts**: `<link rel="preload" as="font" crossorigin>` for fonts
  needed above the fold

### Rendering performance

- **Avoid layout thrashing**: read-then-write patterns that force the browser to
  recalculate layout multiple times per frame. Batch DOM reads, then batch DOM writes
- **`requestAnimationFrame`**: schedule visual updates to align with the browser's
  paint cycle (60fps = ~16ms budget per frame)
- **Web Workers**: offload CPU-intensive computation (encryption, parsing, data transformation)
  to a background thread so the main thread stays responsive
- **Virtual scrolling**: for long lists, render only visible items (react-window, vue-virtual-scroller)

For detailed frontend performance guidance, see `references/frontend_performance.md`.
For detailed database performance guidance, see `references/database_performance.md`.

---

## Caching Strategy

### Cache patterns

| Pattern | How it works | Consistency | Best for |
|---------|-------------|-------------|----------|
| **Cache-aside** | App checks cache first; on miss, loads from DB and populates cache | Eventual (may serve stale data) | Read-heavy data, tolerant of staleness |
| **Read-through** | Cache sits between app and DB; on miss, cache loads from DB transparently | Eventual | Simplifies app code, cache owns DB interaction |
| **Write-through** | Writes go to cache first, then cache syncs to DB | Strong (cache is always current on writes) | Write-heavy data that's also frequently read |
| **Write-behind** | Writes go to cache, cache asynchronously writes to DB | Weak (data loss risk if cache crashes before flush) | High write throughput where some data loss is acceptable |

### Cache invalidation

The two hard problems in computer science: naming things, cache invalidation, and off-by-one errors.

- **TTL (Time to Live)**: simplest — data expires after N seconds. Choose TTL based on
  acceptable staleness (business requirement, not technical convenience)
- **Write-triggered invalidation**: invalidate cache entries when the source data changes.
  Precise but complex — determine which cache keys are affected by each write
- **Cache stampede prevention**: when a hot cache key expires, many requests simultaneously
  hit the database. Mitigate with: probabilistic early recomputation, locking on cache
  miss, or serving stale data while asynchronously refreshing

### What to cache

| Good candidates | Bad candidates |
|----------------|---------------|
| Static assets (images, fonts, CSS) | Frequently changing data (user's latest action) |
| Session data (short TTL) | Payment/billing results (must be authoritative) |
| API responses that are expensive to compute | Data unique to each user (unless TTL is very short) |
| Database query results for read-heavy endpoints | Write-heavy endpoints (cache adds overhead, not value) |
| Auth token validation (short TTL) | Auth credentials themselves (security risk) |

### Caching layers

| Layer | Technology | Typical TTL |
|-------|-----------|-------------|
| Browser cache | HTTP Cache-Control headers, Service Worker Cache API | hours to days |
| CDN | Cloudflare, Fastly, CloudFront | minutes to hours |
| Application cache | Redis, Memcached | seconds to minutes |
| Database cache | PostgreSQL shared_buffers, MySQL buffer pool | automatic (LRU) |
| ORM cache | Django cache framework, Hibernate L2 cache | query/request scope |

---

## Async I/O and Concurrency

### Event loop blocking (Node.js)

Node.js runs JavaScript on a single thread. A long-running synchronous operation blocks
the entire event loop — no other requests can be processed.

**Red flags:**
- Synchronous file I/O (`fs.readFileSync`, `fs.writeFileSync`)
- `JSON.parse()` on large payloads (>1MB)
- Synchronous crypto operations on large data
- Heavy computation in request handlers (tight loops, large sorts, template compilation)
- `Array.prototype.sort()` with a complex comparator on large arrays

**Fixes:**
- Use async equivalents (`fs.promises.readFile`)
- Offload to Worker Threads for CPU-bound work
- Stream processing for large payloads
- Use `setImmediate()` or `process.nextTick()` to break up long-running tasks

### Async I/O (Python)

Python's `asyncio` also uses a single-threaded event loop. Blocking calls in async
functions stall the entire event loop.

**Red flags:**
- `time.sleep()` in an `async def` — use `await asyncio.sleep()` instead
- Synchronous database queries (`psycopg2`) in async functions — use `asyncpg`
- File I/O with `open()` in async functions — use `aiofiles`
- CPU-bound work in async functions — use `loop.run_in_executor()` to run in a thread pool

### Backpressure

When producers generate work faster than consumers can process it, the system needs
to slow down producers, not buffer unboundedly.

**Signals of missing backpressure:**
- Queue depth grows without bound under load
- Memory usage climbs until OOM
- Timeouts cascade as downstream services are overwhelmed

**Solutions by context:**
- **HTTP APIs**: return 429 Too Many Requests + `Retry-After` header
- **Message queues**: set queue max length; consumers signal readiness (pull model
  instead of push)
- **Streams**: reactive backpressure (RxJS, Reactive Streams, Project Reactor)
- **Database connection pools**: bounded queue with timeout — fail fast, don't queue infinitely

---

## Serverless and Cold Starts

### What is a cold start?

When a serverless function is invoked after being idle, the platform must:
1. Provision a container/instance
2. Load the runtime
3. Load and initialize your code (import modules, establish connections)
4. Handle the request

This can add 100ms–10s of latency depending on runtime, package size, and initialization code.

### Cold start optimization

- **Keep packages small**: each MB of dependencies adds to initialization time.
  Tree-shake, remove unused dependencies, prefer slim SDK clients
- **Lazy initialization**: defer non-critical setup (logging, analytics, optional feature
  flags) to after the first response
- **Connection reuse outside handler**: initialize database connections and HTTP clients
  in the global scope (outside the handler function) so they persist across warm invocations
- **Keep-warm strategies**: periodic pings to prevent instances from going cold.
  Be aware of concurrency — a keep-warm ping every minute keeps one instance warm,
  but under load the platform provisions additional cold instances
- **Provisioned concurrency**: pre-warm a specified number of instances (AWS Lambda,
  Cloud Functions). Costs more but guarantees no cold starts for known traffic patterns
- **Runtime choice**: Go and Rust cold start in <100ms; Java and .NET take 1–10s.
  Python and Node.js are in the middle (~200ms–1s)

---

## Performance Measurement

### Percentile-based measurement

Never use average (mean) latency. Distributions are long-tailed — the average hides
slow outliers that some users experience.

| Percentile | Meaning |
|-----------|---------|
| p50 (median) | Half of requests are faster than this. The typical user experience |
| p95 | 5% of users experience latency this high or higher |
| p99 | The worst 1% — these are the users who will complain |
| p99.9 | The tail of the tail — critical for high-reliability services |

**Rule of thumb**: set SLOs on p95 or p99, not on average. "Average response time < 200ms"
is a useless SLO if 1% of requests take 10 seconds.

### Histograms

Percentiles are approximations unless you store every request. Histograms bucket requests
into latency ranges (0-10ms, 10-25ms, 25-50ms, ...) and allow accurate percentile
calculation across any time window. Prefer histogram metrics over summary metrics.

### Load testing methodology

| Test type | Purpose | Duration |
|-----------|---------|----------|
| **Ramp-up** | Find the maximum throughput before degradation | Increase load stepwise until p95 exceeds SLO |
| **Soak** | Detect memory leaks, connection leaks, gradual degradation | Run at 70% of max throughput for 4–24 hours |
| **Spike** | Verify system handles sudden traffic surges | Sudden jump from baseline to 3x, then back |
| **Stress** | Find breaking point and recovery behavior | Increase load until system fails; observe recovery |

### Performance acceptance criteria

Every spec should define performance requirements in concrete, measurable terms:

**Good (measurable):**
- "p95 API latency < 200ms at 1000 RPS per instance"
- "LCP < 2.5s on 3G mobile connection for 90th percentile"
- "Database can sustain 5000 writes/second with <10ms replication lag"

**Bad (unmeasurable):**
- "The system should be fast"
- "Pages should load quickly"
- "The database should handle high load"

---

## Performance Anti-Patterns Checklist

### Data access
- [ ] N+1 queries: loading a list and iterating to load relations
- [ ] `SELECT *` instead of selecting needed columns
- [ ] Missing pagination on potentially large result sets
- [ ] No database query timeout configured
- [ ] Synchronous cache population blocking the request path
- [ ] Missing indexes on columns used in WHERE, JOIN, ORDER BY

### Network and I/O
- [ ] Chatty microservices: 5+ sequential HTTP calls in a single request path
- [ ] No timeout on external API calls
- [ ] No retry with backoff (or retry on non-idempotent operations)
- [ ] Large payloads without compression (gzip/brotli on API responses; image compression)
- [ ] Unbounded queue/message buffer — no backpressure mechanism

### Computation
- [ ] CPU-bound work on the request thread (Node.js event loop, Python async)
- [ ] Unbounded in-memory collections — loading all rows into a list without pagination
- [ ] Repeated expensive computation without memoization or caching
- [ ] Inefficient serialization/deserialization in hot paths

### Frontend
- [ ] No code splitting — entire application JS loaded on first page
- [ ] LCP image is lazy-loaded (delays LCP)
- [ ] Render-blocking JS/CSS in `<head>`
- [ ] No image optimization (wrong resolution, wrong format, no compression)

### Infrastructure
- [ ] No autoscaling configured
- [ ] Cold start > 2s without keep-warm or provisioned concurrency
- [ ] No load shedding or rate limiting
- [ ] Connection pool too small for expected concurrency

---

## Common Risks

- Performance requirements expressed qualitatively ("fast", "responsive") instead of
  with concrete metrics (p95 < 200ms)
- N+1 data access patterns specified or implied by the data model
- Synchronous processing of work that should be asynchronous or queued
- No caching strategy for frequently-read, rarely-changed data
- Unbounded collections or result sets — no pagination or limit
- Chatty cross-service communication with no circuit breakers or timeouts
- CPU-bound work on the main request thread in single-threaded runtimes
- Missing indexes on query patterns implied by the specification's access patterns
- No plan for cold start latency in serverless architectures

## Review questions

- Are performance requirements expressed as concrete metrics (p95/p99 latency, throughput,
  LCP/INP/CLS targets) or as qualitative adjectives?
- Which flows need explicit latency budgets? What is the SLO for each?
- What grows with the number of users, tenants, or records? Is it linear or sub-linear?
- What happens during a 10x traffic spike? Is there rate limiting, load shedding, autoscaling?
- Where does a single slow dependency degrade the entire flow? Are there circuit breakers?
- Are there N+1 data access patterns in the implied or explicit data model?
- Is CPU-bound work on the request thread (Node.js event loop, Python asyncio)?
- Is there a caching strategy for repeated expensive reads? How is invalidation handled?
- Are timeouts configured on every external call?
- What is the cold start latency in the chosen deployment model?
