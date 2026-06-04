# Code Quality and Maintainability Heuristics

## Focus areas

- **Code metrics**: cyclomatic and cognitive complexity, coupling, churn
- **Code rot signals**: structural smells that predict maintenance difficulty
- **Refactoring patterns**: common transformations to improve code health
- **Commented code**: detection, risks, remediation
- **Maintainability signals**: evolvability, change isolation, tech debt
- **Tooling**: static analysis and quality gates per language

---

## Cyclomatic Complexity

### Definition

Cyclomatic complexity measures the number of linearly independent paths through a
function's control flow. Each `if`, `else if`, `for`, `while`, `case`, `&&`, `||`,
`except`, and `? :` adds one to the count.

### Thresholds

| Complexity | Classification | Action |
|-----------|----------------|--------|
| 1–5 | Low | No action needed |
| 6–10 | Low-Medium | Acceptable; consider simplification if logic is non-obvious |
| 11–20 | Complex | Medium risk — refactor opportunistically |
| 21–50 | Very complex | High risk — refactor before adding features |
| >50 | Untestable | Critical risk — must be broken down immediately |

For per-language tooling (ESLint, Radon, PMD, gocyclo, etc.) and detailed metrics
definitions, see `references/code_metrics_reference.md`.

### Cognitive complexity vs cyclomatic

Cognitive complexity weights nesting more heavily than cyclomatic. Prefer cognitive
complexity for readability assessments; cyclomatic for testability.

### Review prompt

For each function in the critical path: what is its cyclomatic complexity? If >10,
can the branching logic be extracted into smaller functions or polymorphic strategies?

---

## Coupling and Churn Metrics

### Key coupling concepts

- **Afferent coupling (Ca)**: number of consumers depending on a package
- **Efferent coupling (Ce)**: number of packages a package depends on
- **Instability (I)**: `Ce / (Ca + Ce)` — 0 is maximally stable, 1 is maximally unstable
- **Abstractness (A)**: ratio of abstract to total classes in a package
- **Distance from Main Sequence (D)**: `|A + I - 1|` — packages with D > 0.5 are in the "zone of pain"

### Code churn risk matrix

| | Low complexity | High complexity |
|---|----------------|-----------------|
| **High churn** | Monitor | **Highest refactoring priority** |
| **Low churn** | Safe | Refactor opportunistically |

For full definitions, formulas, per-language tooling, and the detailed churn+complexity
matrix, see `references/code_metrics_reference.md`.

### Review prompt

Which packages have the highest Distance from Main Sequence? Which files have both
high churn and high complexity? These should be prioritized for simplification and
test coverage.

---

## Code Rot Signals (Structural Smells)

### Shotgun Surgery

A single requirement change forces modifications across many files.

**Detection:** Adding a new field to a data model requires changes in 8+ files
(controller, service, repository, serializer, frontend component, test, migration, docs).

**Fix:** Consolidate related behavior. Use the Single Responsibility Principle
to co-locate things that change together.

### Divergent Change

A single class changes for multiple unrelated reasons.

**Detection:** The `OrderService` class was modified in commits about payment, then
inventory, then notification. The class's git history shows changes from unrelated
features.

**Fix:** Split the class along responsibility boundaries.

### Feature Envy

A method accesses another class's data more than its own.

**Detection:** Method `calculateDiscount()` on `InvoiceService` accesses
`customer.tier`, `customer.loyalty_points`, `customer.annual_spend` —
it belongs on `Customer`.

**Fix:** Move the method to the class whose data it uses most.

### Long Method

A method that does too many things, typically >20 lines.

**Detection:** The method has sections separated by blank lines and comments
explaining what each section does.

**Fix:** Each comment-separated section becomes its own well-named method.

### Large Class

A class with too many responsibilities, typically >200 lines or >10 public methods.

**Detection:** The class's methods reference different subsets of its fields —
the fields cluster into groups that don't interact.

**Fix:** Extract cohesive clusters of fields and methods into new classes.

### Primitive Obsession

Using primitive types (string, int) instead of domain types.

**Detection:** `send_email(to: str, subject: str, body: str)` — `to` could be any
string, not just a valid email. `charge(amount: float)` — floating point for money.

**Fix:** Create value objects: `Email`, `Money`, `PhoneNumber`, `Address`.

### Long Parameter List

Methods with 4+ parameters.

**Detection:** Call sites pass the same group of parameters together repeatedly.
All callers pass `(user_id, user_name, user_email, user_role)`.

**Fix:** Introduce a parameter object that groups related parameters.

### Data Clumps

The same group of fields appears together in multiple places.

**Detection:** `start_date` and `end_date` appear together as parameters in 5+
methods, as fields in 3+ classes.

**Fix:** Extract into a `DateRange` value object.

### Commented-Out Code

Code blocks that are commented out instead of deleted.

**Detection:** Large comment blocks containing what looks like code. The block
has been present for more than one release cycle.

**Risks:**
- Creates confusion: is this code expected to be restored? Under what conditions?
- Decays over time: the surrounding code changes, making the commented code incorrect
- Clutters the file: adds noise that slows down reading
- Version control is the archive: git history preserves the old code if needed

**Fix:**
1. Delete commented-out code immediately
2. If it represents an alternative approach worth preserving, document it in an ADR
   or design doc, not as dead code in the source file
3. If it's a temporary `TODO` note, convert to a ticket with a deadline

### TODO / FIXME / HACK accumulation

**Detection:** More than 5 TODO/FIXME/HACK markers per 1000 lines of code.
Comments older than 6 months without associated tickets.

**Fix:**
- Every TODO must reference a ticket number and be resolved within one sprint
- Every HACK must document: (a) what the correct fix is, (b) under what conditions
  the hack can be removed, (c) how to detect when those conditions are met
- Run a CI check that fails on TODOs older than N days

---

## Refactoring Patterns (Compact Catalog)

| Smell | Refactoring |
|-------|-------------|
| Long Method (>20 lines) | Extract Method |
| Large Class (>200 lines, >10 methods) | Extract Class |
| Primitive Obsession | Replace Data Value with Object |
| Long Parameter List (>3 params) | Introduce Parameter Object |
| Feature Envy | Move Method / Move Field |
| Divergent Change | Extract Class along responsibility |
| Shotgun Surgery | Move Method to co-locate related changes |
| Duplicate Code | Extract Method / Pull Up Method |
| Switch/if-else on type code | Replace Conditional with Polymorphism |
| Complex boolean expression | Decompose Conditional / Extract Method |
| Magic number | Replace Magic Number with Named Constant |
| Dead code (unreachable) | Remove Dead Code |
| Complicated nested conditional | Replace Nested Conditional with Guard Clauses |
| Comments explain what code does | Rename Method (make code self-documenting) |
| Mutable data shared widely | Encapsulate Field / Replace with Immutable Object |

Detailed refactoring catalog with before/after examples: see `references/refactoring_catalog.md`.

---

## Linting and Static Analysis Quality Gates

### Per-language recommendations

| Language | Linter | Type checker | Complexity | Security |
|----------|--------|-------------|------------|----------|
| Python | Ruff / Flake8 | MyPy / Pyright | Radon | Bandit |
| TypeScript | ESLint | tsc --noEmit | ESLint complexity | eslint-plugin-security |
| JavaScript | ESLint | (optional) | ESLint complexity | eslint-plugin-security |
| Java | Checkstyle / SpotBugs | (built-in) | PMD | SpotBugs + FindSecBugs |
| Go | golangci-lint | (built-in) | gocyclo | gosec |
| Rust | clippy | (built-in) | clippy cognitive | cargo-audit |
| Ruby | RuboCop | Sorbet (optional) | RuboCop | Brakeman |
| C# | Roslyn Analyzers | (built-in) | NDepend | Security Code Scan |

### Pre-commit quality gates

Every commit should pass before reaching code review:

1. **Lint** (no style violations)
2. **Type check** (no type errors)
3. **Unit tests** (all passing)
4. **Complexity threshold** (no new functions >10 cyclomatic complexity —
   or at least documented justification for exceptions)

### CI quality gates

CI pipeline should run:

1. Lint + type check
2. Unit tests + coverage report
3. Integration tests
4. Security scan (SAST: Bandit, gosec, eslint-plugin-security)
5. Dependency vulnerability scan (`npm audit`, `pip-audit`, Snyk)
6. Complexity regression check (complexity delta per PR)

---

## Technical Debt Quantification

### Debt interest calculation

When a feature is built on a complex, poorly-structured area of code, that area
exerts an "interest rate" on development:

- Each subsequent feature touching that area takes **X% longer** than it would
  in a clean codebase
- The interest compounds: the longer the debt remains, the more features
  accumulate more complexity

### Prioritization matrix

| | High churn + high complexity | Low churn + high complexity |
|---|---------------------------|----------------------------|
| **Priority** | Pay down immediately | Schedule for next maintenance window |
| **Risk** | Each sprint costs more | Stable but blocks future features |
| **Action** | Dedicated refactoring sprint | Opportunistic refactoring during adjacent feature work |

## Maintainability and Evolvability Signals

- Changes stay localized: a new feature touches 1-2 files, not 15
- Variants can be added without rewriting existing code (OCP compliance)
- Infrastructure details are isolated behind interfaces — swapping databases
  or message queues does not touch business logic
- Interfaces are stable enough that consumers don't break on minor updates
- New team members can understand a module by reading its public interface and tests

## Common Risks

- Functions with cyclomatic complexity >20 in business-critical paths
- Classes that combine data persistence, business rules, and UI formatting
- Commented-out code blocks present in production files
- TODO/FIXME markers older than 6 months without associated tickets
- Repeated bug fixes in the same high-churn file — a signal that the file is
  too complex and needs restructuring
- Business logic duplicated between frontend and backend validation
- Primitive types used where domain value objects would prevent invalid states

## Review questions

- What is the cyclomatic complexity of the 5 most-changed files in the last quarter?
- Which files have both high churn and high complexity? (highest refactoring priority)
- Are there commented-out code blocks that have survived more than one release?
- Do TODO/FIXME/HACK markers reference ticket numbers and have deadlines?
- Which packages have the highest Distance from Main Sequence (D > 0.5)?
- Would a new requirement force changes across many unrelated files? (Shotgun Surgery)
- Does any method access another class's data more than its own? (Feature Envy)
- Are domain concepts represented as primitive types (string email, float money)?
- What is the pre-commit and CI quality gate configuration? Are all gates enabled?
- Is there a complexity regression check in CI?
