# Code Metrics Quick Reference

## Cyclomatic Complexity

Measures independent paths through code. Each `if`, `for`, `while`, `case`, `&&`, `||`,
`except`, `catch`, `?:` adds one.

### Thresholds

| Complexity | Risk | Action |
|-----------|------|--------|
| 1–5 | Low | No action |
| 6–10 | Low-Medium | Acceptable; consider simplification if logic is non-obvious |
| 11–20 | Medium | Refactor opportunistically; extract helper functions |
| 21–50 | High | Must refactor before adding features; split into smaller functions |
| >50 | Critical | Untestable; break down immediately; high bug density |

### Per-language tooling

| Language | Tool | Command |
|----------|------|---------|
| Python | Radon | `radon cc path/ -a -s` |
| Python | Xenon | `xenon --max-absolute B --max-modules A --max-average A path/` |
| TypeScript/JS | ESLint | `complexity: ["error", 10]` in `.eslintrc` |
| TypeScript/JS | SonarJS | SonarQube/SonarCloud analysis |
| Java | PMD | `CyclomaticComplexity` rule (default max: 10) |
| Java | Checkstyle | `CyclomaticComplexity` check |
| Ruby | RuboCop | `Metrics/CyclomaticComplexity` (default max: 7) |
| Go | gocyclo | `gocyclo -over 10 ./...` |
| Rust | clippy | `#[deny(clippy::cognitive_complexity)]` |
| C# | Visual Studio | Code Metrics in Analyze menu |
| PHP | PHPMD | `CyclomaticComplexity` rule |

---

## Cognitive Complexity

Weights nesting more heavily than cyclomatic. A deeply nested `if` scores higher than the
same `if`s sequenced. Prefer this for readability assessments.

### Thresholds (SonarQube scale)

| Score | Risk |
|-------|------|
| 0–15 | Low |
| 16–30 | Medium |
| 31–45 | High |
| >45 | Critical |

### Per-language tooling

| Language | Tool |
|----------|------|
| TypeScript/JS | ESLint: `sonarjs/cognitive-complexity` |
| Java | SonarQube/SonarCloud |
| C# | SonarQube/SonarCloud |
| Python | flake8-cognitive-complexity |
| Ruby | RuboCop: `Metrics/CyclomaticComplexity` cop; `rubycritic` for broader code metrics |
| Go | gocognit |
| Rust | clippy: `cognitive_complexity` lint |

---

## Lines of Code (LOC)

### Function / method size

| Lines | Classification |
|-------|---------------|
| 1–20 | Good — easy to understand |
| 21–50 | Acceptable — consider splitting if logic has distinct sections |
| 51–100 | Warning — likely doing too much; extract helper methods |
| >100 | Critical — almost certainly needs decomposition |

### File / module size

| Lines | Classification |
|-------|---------------|
| 1–200 | Good — focused module |
| 201–500 | Acceptable — monitor for scope creep |
| 501–1000 | Warning — likely has multiple responsibilities |
| >1000 | Critical — split into focused modules |

---

## Coupling Metrics

### Afferent Coupling (Ca)

Number of classes outside this package that depend on classes inside this package.
Higher = more responsibility (more consumers depend on you).

### Efferent Coupling (Ce)

Number of classes outside this package that classes inside this package depend on.
Higher = more fragile (you depend on many things).

### Instability (I)

`I = Ce / (Ca + Ce)`

| I value | Meaning |
|---------|---------|
| 0 | Maximally stable — no dependencies, many dependents |
| 0–0.3 | Very stable — hard to change |
| 0.3–0.7 | Balanced — moderate change difficulty |
| 0.7–1.0 | Unstable — easy to change |
| 1 | Maximally unstable — many dependencies, no dependents |

### Abstractness (A)

`A = abstract_classes_in_package / total_classes_in_package`

| A value | Meaning |
|---------|---------|
| 0 | Fully concrete |
| 0–0.3 | Mostly concrete |
| 0.3–0.7 | Balanced |
| 0.7–1.0 | Mostly abstract |
| 1 | Fully abstract (nothing but interfaces/abstract classes) |

### Distance from Main Sequence (D)

`D = |A + I - 1|`

| D value | Zone | Meaning |
|---------|------|---------|
| 0–0.2 | Sweet spot | Good balance of abstractness and stability |
| 0.2–0.5 | Acceptable | Minor imbalance; monitor |
| 0.5–1.0 | Pain | Significant imbalance — refactor |
| >1.0 | Critical pain | Package is in the "zone of pain" |

**Zone of pain (high D):** Stable but concrete (I ≈ 0, A ≈ 0) — hard to change,
many consumers. *Or* abstract but unstable (I ≈ 1, A ≈ 1) — no consumers, no
need for abstraction. Solution for the former: add interfaces. Solution for the
latter: remove unnecessary abstractions or find consumers.

### Per-language coupling tooling

| Language | Tool |
|----------|------|
| Python | Radon (`radon cc --show-closures`), pybunch |
| Java | JDepend, SonarQube |
| TypeScript/JS | dependency-cruiser, madge |
| Ruby | RuboCop, Reek |
| Go | go-architect, godepgraph |
| C# | NDepend |
| General | SonarQube/SonarCloud |

---

## Code Churn

Measures how frequently a file changes. Combine with complexity to find hotspots.

### Churn calculation

- Count git commits touching the file in the last N months (typically 3–6)
- Alternatively: count lines added + deleted in the period
- Visualization: `git log --format=oneline --name-only --since="6 months ago" | sort | uniq -c | sort -rn`

### Hotspot prioritization matrix

| | Low complexity (1-10) | High complexity (>10) |
|---|---------------------|----------------------|
| **High churn** (>5 changes/quarter) | Monitor — may hide insufficient requirements or tests | **Immediate action** — highest bug-risk area |
| **Low churn** (≤5 changes/quarter) | Safe | Stabilize opportunistically |

### Churn + coverage matrix

| | High churn + low coverage | High churn + high coverage |
|---|-------------------------|--------------------------|
| **Risk** | Very high — changing often, poorly tested | Medium — changing often, well tested |
| **Action** | Write tests before adding features | Monitor; may need refactoring if complexity is also high |

---

## Test Coverage

### Coverage types

| Type | What it measures | Value |
|------|-----------------|-------|
| **Line coverage** | Which lines were executed | Basic — necessary but insufficient |
| **Branch coverage** | Which branches (if/else, switch cases) were explored | Better — catches uncovered paths in covered lines |
| **Mutation coverage** | Whether tests detect intentional bugs (mutations) | Best — validates that tests actually test something meaningful |

### Coverage targets

| Coverage type | Minimum | Good | Excellent |
|--------------|---------|------|-----------|
| Line coverage | 60% | 80% | 90%+ |
| Branch coverage | 50% | 70% | 85%+ |
| Mutation coverage | 20% | 50% | 80%+ |

**Important:** Coverage percentage alone is a vanity metric. 80% line coverage with
no assertions is meaningless. 80% line coverage of critical business logic matters
much more than 80% coverage of getters/setters. Always assess coverage against
**business criticality**, not just percentage.

---

## Maintainability Index (MI)

Composite metric combining: cyclomatic complexity, lines of code, and Halstead volume.

| MI score | Classification |
|----------|---------------|
| 85–100 | Highly maintainable |
| 65–85 | Moderately maintainable |
| 40–65 | Low maintainability — needs refactoring |
| 0–40 | Very low maintainability — high risk |

### Halstead metrics (components of MI)

- **Halstead Volume**: size of implementation (operators + operands × log2)
- **Halstead Difficulty**: how hard the code is to write (unique operators,
  operand count)
- **Halstead Effort**: Volume × Difficulty — estimated effort to implement

### Per-language MI tooling

| Language | Tool |
|----------|------|
| Python | Radon (`radon mi path/`) |
| TypeScript/JS | SonarQube, Plato |
| Java | SonarQube |
| C# | Visual Studio Code Metrics, NDepend |
| PHP | PHPMD |
| General | SonarQube/SonarCloud |

---

## Spec Review Application

When reviewing a specification, use these metrics as **design-time heuristics**:

- **Predict hot spots**: which components implied by the spec will have high complexity?
  High churn? Evaluate whether the design already isolates these or will create fragile code
- **Predict coupling**: which components will depend on many others? Are the dependency
  directions aligned with stability (stable components should not depend on unstable ones)?
- **Assess testability**: will components with high predicted complexity be testable
  in isolation? Or will they require complex integration setups?
- **Predict evolution**: when a likely future requirement arrives, will it touch many
  files (shotgun surgery) or be localized? Use coupling predictions to evaluate

---

## Common Risks

- Code metrics tracked but not acted upon — dashboards without remediation process
- Coverage percentage celebrated without assessing what is covered (getters/setters)
- High-churn files with no additional test investment — each change increases risk
- Stable packages that are entirely concrete (A ≈ 0, I ≈ 0) — changes break many consumers
- Unstable packages that are abstract (A ≈ 1, I ≈ 1) — unnecessary complexity, no consumers
- Cyclomatic complexity limits configured in CI but bypassed with `// NOLINT` or `# noqa`

## Review questions

- What will be the highest-complexity components in the proposed design?
- Does the design isolate complex components so they can be tested and changed independently?
- Which components will depend on the most other components? Are dependency directions correct?
- Is there a plan for measuring and enforcing code metrics (complexity, coverage, coupling)?
- Are CI quality gates configured with concrete thresholds? Are they enforced or advisory?
