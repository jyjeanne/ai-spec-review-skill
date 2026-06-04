# Documentation Review Heuristics

## Focus areas

- **Documentation maturity model**: 5 levels from absent to continuously maintained
- **Documentation types**: API reference, architecture, runbooks, onboarding, ADRs
- **Architecture Decision Records (ADRs)**: why, when, how
- **Changelog conventions**: Keep a Changelog, automated from Conventional Commits
- **Diagrams**: C4 model, sequence diagrams, ERDs, tooling
- **Docs-as-code**: version control, review, CI validation
- **Documentation freshness**: rot detection, last-reviewed dates, automated drift checks
- **Code comments**: what to comment, what never to comment, comment quality signals
- **Operational documentation**: runbooks, incident playbooks, monitoring references

---

## Documentation Maturity Model

| Level | Name | Characteristics |
|-------|------|----------------|
| 0 | **Absent** | No documentation exists beyond the code itself |
| 1 | **Ad-hoc** | Scattered READMEs, some inline comments, no consistent structure. Engineers rely on tribal knowledge |
| 2 | **Standardized** | Consistent template for each doc type. API reference exists. Architecture diagram exists but may be stale. Onboarding doc covers setup |
| 3 | **Integrated** | Docs are in version control alongside code. Docs reviewed in PRs. CI validates docs (broken links, spelling). ADRs for significant decisions. Runbooks link to monitoring dashboards |
| 4 | **Continuously maintained** | Documentation freshness is automatically tracked. Drift between docs and API surface is detected. Changelog is auto-generated from conventional commits. On-call runbooks are tested during game days. Docs-as-code with full CI/CD pipeline |

### Review prompt

At what maturity level is this specification's documentation plan? What is the gap
to the next level?

---

## Documentation Types

### API reference

- Every public endpoint, function, class, or method has a clear contract
- Includes: signature, parameters (with types and constraints), return values,
  error responses/exception types, authentication requirements, rate limits
- Auto-generate where possible (OpenAPI/Swagger for REST, GraphQL introspection,
  JSDoc/Sphinx for code)
- Example: `GET /users/:id` — what happens when the user doesn't exist? When the
  caller is not authenticated? When the ID format is invalid?

### Architecture overview

- System context diagram: what are the external systems, users, and boundaries?
- Container diagram: what are the deployable units (web app, API, database, queue)?
- Component diagram: what are the major modules within each container?
- Key design decisions: why was this architecture chosen over alternatives?
- Integration contracts: how do components communicate (REST, gRPC, events, message queue)?

### Getting-started / onboarding

- Prerequisites: what must be installed (language version, database, tools)?
- Setup steps: commands to clone, install dependencies, configure, and run locally
- "Hello world" walkthrough: a minimal end-to-end flow
- Common issues and troubleshooting during setup

### Runbooks

- For each alert: what does it mean, what is the impact, how to triage, how to mitigate?
- Health check endpoints and what they verify
- Log locations and how to search them
- Feature flag configuration and how to toggle features in emergencies

### Troubleshooting guide

- Common failure modes and their symptoms
- Diagnostic commands and what output to look for
- Escalation path for unresolved issues

### Architecture Decision Records (ADRs)

ADRs document significant architectural decisions, the context at the time, and the
consequences of the decision.

**Template:**

```markdown
# ADR-{NNN}: {Title}

**Status:** proposed | accepted | deprecated | superseded by ADR-XXX

**Date:** YYYY-MM-DD

**Context:**
What is the problem we're solving? What constraints exist?

**Decision:**
What did we decide? Be specific: this is the architecture we are committing to.

**Consequences:**
What becomes easier? What becomes harder? What are the risks and tradeoffs?
```

**When to write an ADR:**
- Choosing between two or more architectural approaches (SQL vs NoSQL, monolith vs microservices)
- Introducing a new pattern, library, or technology (adopting GraphQL, switching ORMs)
- Establishing a cross-cutting convention (API versioning strategy, error handling standard)
- Deprecating a system or pattern

**Storage convention:** `docs/adr/` directory, numbered sequentially (ADR-001, ADR-002).
Refer to ADRs from code when the code exists only because of that decision.

---

## Changelog Conventions

### Keep a Changelog format

- File: `CHANGELOG.md` in the repo root
- Sections: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`
- Each entry is a bullet describing the change in user-facing terms
- Human-readable, not a raw commit log

### Automated from Conventional Commits

If the project uses Conventional Commits (`feat:`, `fix:`, `BREAKING CHANGE:`), automate
changelog generation with tools like `standard-version`, `semantic-release`, or
`release-please`.

Commit format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

- `feat:` → MINOR version bump, appears under `Added`
- `fix:` → PATCH version bump, appears under `Fixed`
- `BREAKING CHANGE:` in footer → MAJOR version bump, appears under `Changed` with migration notes

---

## Diagrams

### C4 Model (Context → Container → Component → Code)

Prefer C4 over ad-hoc box-and-line diagrams. C4 provides a consistent, zoomable
view of the system.

| Level | Audience | Content |
|-------|----------|---------|
| **System Context** | Everyone | The system and its users/external dependencies (1 diagram) |
| **Container** | Technical people | Deployable units: web app, API, database, message queue, blob storage |
| **Component** | Developers | Major structural building blocks within a container |
| **Code** | Developers | Class diagrams, ERDs (auto-generate from code) |

### Sequence diagrams

Use for critical flows: authentication, payment processing, data ingestion pipeline.
Show the order of interactions between components. Essential for understanding
distributed system behavior.

### ERDs (Entity-Relationship Diagrams)

For data models: entities, relationships, cardinality, key fields. Auto-generate
from database schema or ORM models when possible.

### Diagram tooling

- **Mermaid**: text-based, version-controllable, renders in GitHub/GitLab markdown
- **PlantUML**: text-based, more expressiveness than Mermaid, wider diagram type support
- **Structurizr DSL**: C4-optimized, text-based, generates C4 diagrams from code
- **Diagrams as code**: prefer text-based formats over drag-and-drop tools (Visio, draw.io) — they're
  version-controllable, diffable, and reviewable in PRs

---

## Docs-as-Code

### Principles

- Documentation lives in the same repository as the code it documents
- Documentation changes go through the same PR review process as code changes
- Documentation is versioned alongside code — when a feature changes, its docs change
  in the same commit
- CI validates documentation: broken links, spelling, code examples compile/run

### Tooling

| Tool | Best for |
|------|----------|
| MkDocs + Material theme | Python projects, static site, excellent navigation |
| Docusaurus | React ecosystem, versioned docs, blog support |
| VitePress | Vue ecosystem, fast builds, Vue components in docs |
| Sphinx | Python API documentation, auto-generated from docstrings |
| Storybook | UI component libraries |
| OpenAPI / Swagger UI | REST API reference |
| GitHub/GitLab Pages | Free hosting for static doc sites |

### CI validation checks

- [ ] **Broken links**: `markdown-link-check`, `lychee`, or `htmltest` to find dead links
- [ ] **Spelling**: `cspell`, `vale`, or `write-good` for prose linting
- [ ] **Code examples**: extract and run code blocks from markdown to verify they work
  (Docusaurus `remark-mdx-code-blocks`, custom scripts)
- [ ] **API doc coverage**: check that every public endpoint/function has documentation
  (coverage gap detection)

---

## Documentation Freshness

### Rot detection

Documentation rots when:
- The code changes but the documentation does not
- Examples reference removed or renamed functions
- Screenshots show old UI
- API endpoint documentation lists wrong parameters
- Setup instructions reference outdated tool versions

### Freshness signals

- **"Last reviewed" dates** on every document: `<!-- Last reviewed: 2025-06-01 -->`
  in the document header. CI flags documents not reviewed in the last N months
- **Automated API doc drift detection**: compare the OpenAPI spec against the actual
  API responses; compare TypeScript type declarations against actual exports
- **Code example testing**: if doc examples are extracted and run in CI, they naturally
  stay fresh — a broken example fails the build
- **Screenshot/screen recording freshness**: harder to automate, but note the
  application version in the screenshot filename or caption

### Review prompt

How does the specification ensure documentation stays current as the system evolves?
Are there freshness checks, automated or manual?

---

## Code Comments

See `references/clean_code.md` for detailed comment guidance. Summary for spec review:

- **What to comment**: why, not what. Algorithm rationale, workarounds, magic number origins,
  public API contracts
- **What never to comment**: obvious code, commented-out code blocks (use version control),
  manual changelogs in file headers, journal-style comments (`# 2021-03-15 changed by Bob`)
- **TODO comments**: must reference a ticket number and have a resolution deadline.
  TODOs without tickets become permanent dead weight
- **HACK comments**: must document (a) what the correct fix is, (b) conditions under which
  the hack can be removed, (c) how to detect those conditions

---

## Operational Documentation

### Runbook structure

For each alert or incident type:

```markdown
# Alert: {Name}

**Severity:** P1 | P2 | P3
**Alert source:** {Prometheus/Grafana alert name}
**Monitoring dashboard:** {link}

## What it means
Describe the condition that triggers this alert in plain language.

## Impact
What is affected? Who is affected? What is the blast radius?

## Triage
1. Check dashboard {link} for anomaly correlation
2. Check logs with query: `{exact log query}`
3. Check recent deployments: {deployment dashboard link}

## Mitigation
1. {Immediate action to stop the bleeding}
2. {Diagnostic action to confirm root cause}
3. {Long-term fix if known}

## Escalation
If unresolved after {N} minutes, escalate to {team/on-call rotation}.
```

### Incident response playbooks

- Incident severity classification (SEV1/SEV2/SEV3 with definitions)
- Communication templates (status page updates, internal announcements)
- Post-incident review template (what happened, timeline, impact, root cause,
  action items with owners and deadlines)

---

## Common Gaps

- No ADR process — architectural decisions are made in Slack and lost to history
- Changelog is a raw git log — not useful for users or stakeholders
- Architecture diagram exists only in someone's head or on a whiteboard photo from 2023
- API documentation lists parameters but does not specify error responses or edge cases
- Setup instructions fail for new team members because undocumented prerequisites exist
- Runbooks reference monitoring dashboards by name but no links are provided
- Commented-out code blocks accumulate because "we might need it later"
- TODOs are years old and the original author has left the team
- Documentation lives in a separate wiki that nobody updates — it diverged from the
  codebase 2 years ago

## Review questions

- What documentation maturity level does the specification target? Is it realistic
  for the team and timeline?
- Are there ADRs or their equivalent for the key architectural decisions implied
  by the spec?
- Is the changelog process defined? Will it be automated from Conventional Commits?
- Are diagrams version-controllable (Mermaid, PlantUML) or will they be drag-and-drop
  files that can't be reviewed in PRs?
- How will documentation freshness be maintained? Are there automated checks planned?
- Do runbooks exist for each alert condition the system will generate?
- Are the operational teams (on-call, support) equipped with sufficient documentation
  to triage issues without escalating to developers?
- Is there a defined process for updating documentation when features change? Is it part
  of the Definition of Done?
- Are there any commented-out code blocks in the current codebase? What is the threshold
  for removal?

## Review rule

- If engineers would need to guess behavior during implementation, operations, or
  incident response, treat it as a documentation gap.
