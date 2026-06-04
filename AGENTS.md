# AGENTS.md

## Project identity

This is an **AI skill package**, not a conventional application — there is no build, lint, typecheck, or run command.

## Source of truth

- **`SKILL.md`** is authoritative for the skill contract, output schema, review steps, scoring, and behavior rules. Any change to review dimensions, schema, or scoring must start there.
- `.github/copilot-instructions.md` contains additional session conventions.
- `references/*.md` are grounding heuristics (one per review dimension). When adding a dimension, create the reference file there.

## Commands

- **Run tests** (repo root): `python3 -m unittest scripts.test_review_spec -v`
- **Run preflight helper**: `python3 scripts/review_spec.py path/to/spec.md`

## Enums (must stay consistent across all files)

- **Severity**: `low | medium | high | critical`
- **Confidence**: `high | medium | low`
- **Verdict**: `ready | ready_with_risks | not_ready`
- **Category / Score dimension**: `spec | business_logic | architecture | performance | security | testing | devops | dependencies | standards | ux | documentation | code_quality | maintainability`
- `score.overall` is a holistic judgment, **not** a simple average. Security, business logic, and architecture weigh more heavily.

## Key constraints

- The helper script (`review_spec.py`) is narrow by design: it emits only `summary`, `risk_register`, and `issues`. It does NOT perform domain reviews, generate test plans, or produce scores. Currently covers 6 of 13 categories (spec, testing, security, performance, devops, documentation).
- `business_logic_review.edge_cases` must have corresponding entries in `test_plan.edge_cases` (or be noted as out of scope).
- Python: PEP 8 with type hints. Markdown: ATX headings, prefer bullets.
- PRs require passing tests before submission.
- Reference files are now 26: 18 original + 8 new (`api_design_reference.md`, `code_metrics_reference.md`, `database_performance.md`, `dependency_management_guide.md`, `frontend_performance.md`, `observability_reference.md`, `refactoring_catalog.md`, `threat_modeling_guide.md`).
