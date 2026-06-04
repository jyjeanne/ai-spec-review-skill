# Standards and Norms Review Heuristics

## Focus areas

- **Compliance and regulatory standards**: PCI-DSS, HIPAA, GDPR, SOC2, ISO 27001
- **Accessibility standards**: WCAG 2.1/2.2, ARIA, inclusive design
- **API design conventions**: REST, GraphQL, gRPC style guides
- **Language-specific style guides**: naming, formatting, idioms
- **Versioning conventions**: SemVer, CalVer, API versioning strategies
- **Internationalization (i18n) and localization (l10n)**
- **Commit conventions**: Conventional Commits, commit message standards
- **Code review standards**: checklist for review thoroughness

---

## Compliance and Regulatory Standards

### PCI-DSS (Payment Card Industry Data Security Standard)

**Applies when:** The system processes, stores, or transmits payment card data.

**Key requirements for specs:**
- Cardholder data must be encrypted at rest and in transit (TLS 1.2+)
- Never store CVV/CVC codes after authorization
- Access to cardholder data must be on a need-to-know basis
- All access to cardholder data must be logged and auditable
- Vulnerability scans required quarterly; penetration testing annually
- If the spec mentions payment processing, it MUST address PCI-DSS scope (or explicitly
  state that a compliant third-party processor handles all card data)

### HIPAA (Health Insurance Portability and Accountability Act)

**Applies when:** The system handles Protected Health Information (PHI) in the US.

**Key requirements for specs:**
- PHI must be encrypted at rest and in transit
- Access controls with unique user identification
- Audit controls: record and examine all access to PHI
- Integrity controls: ensure PHI is not altered or destroyed improperly
- Transmission security: protect PHI when transmitted over networks
- Business Associate Agreements (BAAs) with all third-party service providers
- If the spec involves health data, it MUST address these controls

### GDPR (General Data Protection Regulation)

**Applies when:** The system processes personal data of EU residents.

**Key requirements for specs:**
- Lawful basis for processing (consent, contract, legitimate interest, etc.)
- Data minimization: only collect what is necessary
- Right to access, rectify, and delete personal data ("right to be forgotten")
- Data portability: users must be able to export their data in a machine-readable format
- Data breach notification within 72 hours
- Data Protection Impact Assessment (DPIA) for high-risk processing
- Data Processing Agreements (DPAs) with processors
- If the spec involves user data, it MUST address GDPR compliance

### SOC 2 (Service Organization Control 2)

**Applies when:** The system is a SaaS product handling customer data.

**Key trust service criteria:**
- **Security**: protection against unauthorized access
- **Availability**: system is operational and usable as committed
- **Processing integrity**: processing is complete, valid, accurate, timely, authorized
- **Confidentiality**: confidential information is protected
- **Privacy**: personal information is collected, used, retained, disclosed, and disposed
  of appropriately

### ISO 27001

**Applies when:** The organization seeks formal information security certification.

**Requires:**
- Information Security Management System (ISMS)
- Risk assessment and treatment methodology
- Statement of Applicability (which controls from Annex A are applied)
- Continuous monitoring and improvement

### Review prompt

Does the specification name any compliance frameworks? If the domain implies one
(payments → PCI-DSS, health → HIPAA, EU users → GDPR, SaaS → SOC 2), is it addressed?

---

## Accessibility Standards

### WCAG 2.1 / 2.2 (Web Content Accessibility Guidelines)

| Level | Meaning | Requirement |
|-------|---------|-------------|
| **A** | Minimum | Basic accessibility — no keyboard traps, text alternatives for images, captions for video |
| **AA** | Standard (legal requirement in many jurisdictions) | Color contrast ≥4.5:1, focus indicators visible, consistent navigation, error suggestions |
| **AAA** | Highest | Color contrast ≥7:1, sign language for video, no time limits (except non-interactive media) |

**Key WCAG principles (POUR):**
- **Perceivable**: users must be able to perceive the information (text alternatives,
  captions, adaptable content)
- **Operable**: users must be able to operate the interface (keyboard accessible,
  enough time, no seizure-inducing content, navigable)
- **Understandable**: users must be able to understand the information and interface
  (readable, predictable, input assistance)
- **Robust**: content must be robust enough for assistive technologies (compatible
  with current and future user agents)

**Spec review signals:**
- Does the spec mention accessibility at all? If the system has a UI, WCAG AA is
  the minimum expectation
- Are form errors communicated to screen readers (`aria-describedby`, `aria-live`)?
- Is keyboard navigation defined for all interactive elements?
- Are color choices specified with accessible contrast ratios?
- Is `prefers-reduced-motion` respected for animations?

### ARIA (Accessible Rich Internet Applications)

- Use ARIA only when native HTML semantics are insufficient
- First rule of ARIA: don't use ARIA if native HTML provides the semantics (`<button>`
  over `<div role="button">`)
- Required ARIA attributes for custom widgets: role, state, properties

---

## API Design Conventions

For complete REST, GraphQL, gRPC, and API versioning conventions including detailed
examples, status code tables, and pagination strategies, see `references/api_design_reference.md`.
This section provides a summary for standards-compliance review.

### REST conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Resource naming | Plural nouns, kebab-case | `/users`, `/order-items` |
| HTTP methods | GET (read), POST (create), PUT/PATCH (update), DELETE (delete) | `POST /users` |
| Status codes | Use standard codes correctly | 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity, 429 Too Many Requests, 500 Internal Server Error |
| Pagination | Cursor-based preferred for large datasets; offset-based acceptable for small | `?cursor=abc&limit=20` or `?page=2&per_page=50` |
| Filtering | Query parameters on the collection | `?status=active&role=admin` |
| Sorting | `sort` parameter with `-` for descending | `?sort=-created_at,name` |
| Field selection | `fields` parameter for sparse responses | `?fields=id,name,email` |
| Versioning | URL path `/v1/users` or Accept header `application/vnd.api+v1+json` | See versioning section below |
| Error format | Consistent envelope with code + message + details | `{ "error": { "code": "VALIDATION_ERROR", "message": "...", "details": [...] } }` |

### GraphQL conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Type naming | PascalCase | `User`, `OrderItem` |
| Field naming | camelCase | `createdAt`, `totalPrice` |
| Connections | Relay Connection spec for paginated lists | `users(first: 10, after: "cursor") { edges { node { id, name } } }` |
| Mutations | Verb + noun, single input argument | `createUser(input: CreateUserInput!): User!` |
| Errors | Use `errors` array with `extensions` for machine-readable codes | `{ "errors": [{ "message": "...", "extensions": { "code": "UNAUTHENTICATED" } }] }` |
| Nullability | Fields are nullable by default | Mark required fields with `!` |
| Deprecation | `@deprecated(reason: "...")` directive | Document migration path in reason |
| Introspection | Disable in production | `introspection: false` (Apollo), `disable_introspection()` (Graphene) |

### gRPC conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Service naming | PascalCase + `Service` suffix | `UserService` |
| RPC naming | PascalCase verb + noun | `GetUser`, `ListUsers`, `CreateUser` |
| Message naming | PascalCase noun | `User`, `CreateUserRequest`, `CreateUserResponse` |
| Field naming | snake_case | `user_id`, `created_at` |
| Backward compatibility | Never remove fields; use `reserved` keyword | `reserved 3, 5;` |
| Error model | Use `google.rpc.Status` with rich error details | Status code + details |
| Streaming | `stream` keyword on request, response, or both | `rpc WatchEvents(EventFilter) returns (stream Event)` |

### API versioning tradeoffs

| Strategy | Pros | Cons |
|----------|------|------|
| **URL path** (`/v1/users`) | Simplest; visible; easy to route | URL is not truly RESTful (resource identity changes); requires URL changes everywhere |
| **Accept header** (`Accept: application/vnd.api.v1+json`) | Resource URL stays stable; RESTful | Harder to test in browser; more complex routing; caching can be tricky |
| **Query parameter** (`/users?version=1`) | Simple; browser-testable | Not RESTful; encourages forgetting version; not cache-friendly |

**Recommendation:** URL path for public APIs (simplicity > purity). Accept header for
internal APIs where consumers are known and tooling supports it.

---

## Language-Specific Style Guides

| Language | Primary style guide | Formatter |
|----------|-------------------|-----------|
| Python | PEP 8 | Ruff, Black, isort |
| TypeScript/JS | Airbnb JS style guide, Google TS style | Prettier, ESLint |
| Java | Google Java Style | google-java-format, Spotless |
| Go | Effective Go, Go Code Review Comments | gofmt, goimports |
| Ruby | Ruby Style Guide (bbatsov) | RuboCop |
| Rust | Rust Style Guide (rustfmt defaults) | rustfmt, clippy |
| C# | Microsoft C# Coding Conventions | dotnet format |
| PHP | PSR-12 | PHP-CS-Fixer, Laravel Pint |
| Swift | Swift API Design Guidelines | swift-format |

### Key conventions to verify in spec review

- Is the spec's API naming consistent with the language's conventions (camelCase for JS,
  snake_case for Python/Go, PascalCase for C#)?
- Are formatting and linting tools configured as pre-commit hooks or CI gates?
- Does the spec assume or mandate a particular style guide for the team?

---

## Versioning Conventions

### Semantic Versioning (SemVer)

`MAJOR.MINOR.PATCH`

| Bump | When |
|------|------|
| **MAJOR** | Incompatible API changes, breaking changes |
| **MINOR** | Backward-compatible new functionality |
| **PATCH** | Backward-compatible bug fixes |

### Calendar Versioning (CalVer)

Format: `YYYY.MINOR.MICRO` or `YYYY.MM.DD`

**When to use:** When the project has no stable API to track (e.g., Ubuntu releases,
continuous delivery tools), or when the primary consumer concern is "how recent is this?"

### Date-based versioning

`YYYY.MM` or `YYYY.MM.DD`

**When to use:** Documentation, datasets, and artifacts where freshness matters more
than compatibility.

### Spec review signal

Does the specification define a versioning scheme? If SemVer, are breaking changes
clearly differentiated from non-breaking ones in the spec's change plan?

---

## Internationalization (i18n) and Localization (l10n)

### Standards and libraries

- **CLDR** (Common Locale Data Repository): Unicode standard for locale-specific
  formatting — don't reinvent date/number/currency formatting
- **ICU Message Format**: standard syntax for complex message interpolation with
  pluralization and gender: `{count, plural, one {1 item} other {# items}}`
- **BCP 47 language tags**: standard format for locale identifiers (`en-US`, `fr-CA`,
  `zh-Hans-CN`)
- **Unicode**: support UTF-8 throughout the stack. Never assume ASCII

### What must be localizable

- UI strings (labels, buttons, tooltips, placeholders)
- Date, time, and number formatting per locale
- Currency display (`$1,234.56` vs `1.234,56 €` vs `¥1,235`)
- Right-to-left (RTL) layout for Arabic, Hebrew, Farsi, Urdu
- Plural forms (many languages have more complex plural rules than English:
  Russian has 4 forms, Arabic has 6)
- Error messages (user-facing errors, not developer-facing log messages)
- Email/SMS templates

### What should NOT be localized

- Code identifiers (variable names, function names, API field names)
- Log messages (developers and operators need a single language to search across all instances)
- Database values (store canonical values; format at the presentation layer)
- URLs and API paths (use English identifiers)

### Spec review signals

- Does the specification address multiple languages if the user base is international?
- Are UI strings designed for text expansion? (English text often expands 30-40% in
  German, French, Spanish — UIs that don't account for this will break)
- Does the design support RTL layout if applicable?
- Are date/time formats using locale-aware formatting, not hardcoded patterns?

---

## Commit Conventions

### Conventional Commits

```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

| Type | Description | Version bump |
|------|-------------|-------------|
| `feat:` | New feature | MINOR |
| `fix:` | Bug fix | PATCH |
| `docs:` | Documentation only | — |
| `style:` | Formatting, missing semicolons (no code change) | — |
| `refactor:` | Code change that neither fixes nor adds a feature | — |
| `perf:` | Performance improvement | PATCH |
| `test:` | Adding or correcting tests | — |
| `chore:` | Build process or tooling changes | — |
| `ci:` | CI configuration changes | — |
| `BREAKING CHANGE:` | Footer indicating breaking API change | MAJOR |

### Commit message best practices

- Subject line: imperative mood, present tense ("Add feature" not "Added feature")
- Subject line: max 72 characters
- Body: explain WHAT and WHY, not HOW (the code shows HOW)
- Reference issue/ticket numbers in footer: `Closes #123`

### Review prompt

Does the spec define or assume commit conventions? If Conventional Commits are used,
tooling (semantic-release, commitlint) should be configured.

---

## Code Review Standards

### Minimum review checklist

- [ ] Code follows project style guide and passes lint
- [ ] Tests cover the change (new feature → new tests; bug fix → regression test)
- [ ] No commented-out code introduced
- [ ] No secrets or credentials in code, config, or comments
- [ ] Error handling covers expected failure modes
- [ ] Logging is appropriate: sufficient for debugging, not excessive, no PII in logs
- [ ] API changes are documented and versioned appropriately
- [ ] Database migrations are backwards-compatible or have a rollout plan
- [ ] Performance implications considered (N+1 queries, missing indexes, blocking calls)
- [ ] Security implications considered (auth, authorization, input validation, data exposure)

---

## Common Gaps

- Compliance frameworks (PCI-DSS, HIPAA, GDPR) are not mentioned even though the domain
  requires them
- Accessibility is treated as "nice to have" rather than a requirement (WCAG AA is law
  in many jurisdictions for public-facing services)
- API responses have no consistent error envelope — some return `{ error: "msg" }`,
  others return plain strings
- Versioning is not planned — "we'll figure it out when we need v2" → v1 consumers
  break when v2 is introduced
- SemVer is declared but breaking changes are made in MINOR versions
- Internationalization is deferred: strings are hardcoded in English, date formats
  assume US locale, RTL layout is untested
- Commit messages are inconsistent or empty — changelog automation is impossible
- Code review has no checklist — PRs are approved based on "looks good to me"

## Review questions

- Which compliance frameworks does the domain require? Are they addressed?
- Is WCAG AA accessibility planned for any user-facing interface? Is there a specific
  plan for keyboard navigation, screen reader support, and color contrast?
- Are API contracts consistent with the ecosystem's conventions (REST resource naming,
  GraphQL field naming, gRPC message format)?
- Is the API versioning strategy defined? How will breaking changes be communicated
  to consumers?
- Is a versioning scheme (SemVer / CalVer) defined for the system and its APIs?
- If the user base is international, are i18n/l10n requirements defined? Are UI strings
  designed for text expansion and RTL layout?
- Is a commit convention defined? Will changelogs be automated?
- Is there a code review checklist or process defined?

## Review rule

- Prefer explicit standards from the specification first.
- When inferring a norm, state that it is an assumption.
- Flag when the domain implies a standard (PCI-DSS for payments, GDPR for EU data)
  but the specification does not address it.
