# AI Spec Review Skill

> A comprehensive AI skill that reviews markdown specifications through **16 engineering steps** and produces structured, actionable output — risk registers, scored dimensions, test plans, and implementation tasks.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Skill version](https://img.shields.io/badge/skill-v2.2.0-green.svg)](SKILL.md)

---

## Why this skill?

Most spec reviews stop at "looks good" or catch only surface issues. This skill acts as a **principal-engineer-level reviewer** that systematically challenges a specification before a single line of code is written.

It doesn't just summarize — it surfaces ambiguities, contradictions, security gaps, missing edge cases, and operational blind spots, then packages everything into a format that drives engineering planning.

## Review dimensions

| # | Dimension | Grounding reference |
|---|-----------|-------------------|
| 0 | Scope resolution & context loading | `references/language_security_patterns.md` |
| 1 | Specification quality | `references/spec_review.md` |
| 2 | Business logic | `references/business_logic_review.md` |
| 3 | Architecture & API design | `references/architecture_review.md`, `references/api_design_reference.md` |
| 4 | Performance & scalability | `references/performance_review.md`, `references/frontend_performance.md`, `references/database_performance.md` |
| 5 | Security (OWASP Top 10) | `references/owasp_top10.md`, `references/security_vulnerability_patterns.md`, `references/secret_management_checklist.md`, `references/language_security_patterns.md`, `references/threat_modeling_guide.md` |
| 6 | Testing strategy & quality | `references/testing_best_practices.md` |
| 7 | DevOps / CI / CD | `references/devops_ci_cd.md`, `references/observability_reference.md` |
| 8 | Dependency & supply chain | `references/dependency_review.md`, `references/dependency_management_guide.md`, `references/vulnerable_packages_watchlist.md` |
| 9 | Standards & norms | `references/standards_and_norms.md` |
| 10 | UX | `references/ux_review.md` |
| 11 | Documentation | `references/documentation_review.md` |
| 12 | Code quality & maintainability | `references/code_quality_maintainability.md`, `references/clean_code.md`, `references/design_patterns.md`, `references/code_metrics_reference.md`, `references/refactoring_catalog.md` |
| 13 | Test plan generation | `references/testing_best_practices.md` |
| 14 | Task breakdown | *(output-focused, no heuristic reference)* |
| 15 | Self-verification pass | *(cross-cutting quality gate)* |

Each dimension is scored **0–10** using a five-band rubric (Critical / Weak / Adequate / Good / Excellent). The overall score is a holistic judgment, not a simple average — security, business logic, and architecture weigh more heavily.

## Structured output

The skill produces a YAML-structured review containing:

```
summary          → verdict (ready / ready_with_risks / not_ready), top risks, assumptions
issues[]         → title, severity, confidence, category, evidence, impact, recommendation
risk_register[]  → id, severity, likelihood, trigger, mitigation, owner
*_review         → dimension-specific findings (13 sections)
test_plan        → coverage matrix, edge cases, contract tests
tasks[]          → prioritized implementation tasks with acceptance criteria
score            → 14 dimension scores (0–10) + holistic overall
```

See [SKILL.md](SKILL.md) for the complete schema and field guidance.

### What's new in v2.2.0

* **8 new reference files**: `api_design_reference.md`, `code_metrics_reference.md`, `database_performance.md`, `dependency_management_guide.md`, `frontend_performance.md`, `observability_reference.md`, `refactoring_catalog.md`, `threat_modeling_guide.md`
* **Deep rewrites** of 6 existing files: `clean_code.md` (SOLID principles with code examples, naming conventions, FP patterns, dependency injection), `design_patterns.md` (6→20+ patterns + 7 anti-patterns + decision guide), `code_quality_maintainability.md` (cyclomatic complexity thresholds, coupling metrics, code churn, 10 code rot signals, linting quality gates), `performance_review.md` (profiling methodology, database-specific guidance, Core Web Vitals, caching patterns, async I/O, serverless cold starts), `documentation_review.md` (5-level maturity model, ADR template, C4 diagrams, docs-as-code CI validation, freshness detection), `standards_and_norms.md` (compliance frameworks: PCI-DSS/HIPAA/GDPR/SOC2, WCAG accessibility, REST/GraphQL/gRPC conventions, SemVer/CalVer, i18n/l10n standards)
* **Preflight helper expanded**: now detects 6 of 13 categories (spec, testing, security, performance, devops, documentation), up from 4. Expanded security terms (+12), performance terms (+9), and added word-boundary matching to eliminate SLA/SLO false-positives in words like "translate" and "slowly". Severity validation added to `create_issue`.
* **Bug fixes from code review**: PostgreSQL connection count corrected (200-400 → 100-200), cyclomatic complexity tier mismatch resolved across files, NDepend reclassified from Java to C# tooling, duplicate `ci/cd` term removed, `\bunit\b` false positive fixed (no longer matches "business unit"), multi-word term matching handles newlines/tabs/underscores, deduplication of coupling/churn/complexity content between `code_metrics_reference.md` and `code_quality_maintainability.md`

## Install

### As a Copilot / Codex skill

```bash
# Clone into your skills directory
git clone https://github.com/jyjeanne/ai-spec-review-skill.git ~/.codex/skills/ai-spec-review

# Or for other AI runtimes, clone into their equivalent skills directory
```

### As a standalone tool

```bash
git clone https://github.com/jyjeanne/ai-spec-review-skill.git
cd ai-spec-review-skill

# Run the preflight helper on any spec
python3 scripts/review_spec.py path/to/your-spec.md
```

The preflight helper performs lightweight text heuristics (marker detection, testing/security/performance/devops/documentation gap analysis) and outputs JSON with `summary`, `risk_register`, and `issues`. It covers 6 of 13 review categories — intentionally narrower than the full AI-driven review.

## Usage

### With an AI assistant

```
Review this specification using ai-spec-review skill
```

```
Review this specification with ai-spec-review and focus on security, performance, and business logic gaps
```

```
Use ai-spec-review to produce a structured architecture, testing, DevOps, and documentation review
```

### Preflight helper (CLI)

```bash
python3 scripts/review_spec.py spec.md
```

Output example:

```json
{
  "summary": {
    "verdict": "not_ready",
    "top_risks": ["No testing strategy defined", "No security considerations mentioned"],
    ...
  },
  "risk_register": [ ... ],
  "issues": [ ... ]
}
```

## Running tests

```bash
cd scripts
python3 -m unittest test_review_spec -v
```

103 unit tests cover all helper functions: marker detection, word-boundary matching, gap detectors, verdict logic, risk register construction, and CLI integration.

## Repository structure

```
.
├── SKILL.md                      # Skill contract (source of truth)
├── README.md
├── LICENSE
├── .gitignore
├── .github/
│   └── copilot-instructions.md   # Copilot session guidance
├── references/                   # Grounding heuristics (26 files)
│   ├── spec_review.md
│   ├── business_logic_review.md
│   ├── architecture_review.md
│   ├── api_design_reference.md
│   ├── performance_review.md
│   ├── frontend_performance.md
│   ├── database_performance.md
│   ├── owasp_top10.md
│   ├── security_vulnerability_patterns.md
│   ├── secret_management_checklist.md
│   ├── language_security_patterns.md
│   ├── threat_modeling_guide.md
│   ├── vulnerable_packages_watchlist.md
│   ├── testing_best_practices.md
│   ├── devops_ci_cd.md
│   ├── observability_reference.md
│   ├── dependency_review.md
│   ├── dependency_management_guide.md
│   ├── standards_and_norms.md
│   ├── ux_review.md
│   ├── documentation_review.md
│   ├── code_quality_maintainability.md
│   ├── code_metrics_reference.md
│   ├── clean_code.md
│   ├── design_patterns.md
│   └── refactoring_catalog.md
├── scripts/
│   ├── review_spec.py            # Preflight helper
│   └── test_review_spec.py       # Unit tests (82 tests)
└── docs/
    └── samples/                  # Example review artifacts
```

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request.

Key guidelines:

- **SKILL.md is the source of truth** — any change to review dimensions, output schema, or behavior rules starts there
- **Back dimensions with references** — heuristics belong in `references/*.md`, not buried in SKILL.md
- **Keep the helper narrow** — `review_spec.py` is a preflight tool, not the full review engine
- **Run the tests** — `python3 -m unittest test_review_spec -v` must pass before submitting

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
