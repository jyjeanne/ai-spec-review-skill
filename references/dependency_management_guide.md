# Dependency Management Guide

## Focus areas

- **Dependency evaluation rubric**: how to assess a new dependency
- **Version pinning strategy**: exact, range, lockfile-only
- **Supply chain security**: SLSA, Sigstore, SBOM, provenance
- **License compliance**: permissive vs copyleft, compatibility matrix
- **Automated tooling**: Dependabot, Renovate, Snyk, OSV-Scanner
- **Fork vs wrap vs replace**: decision matrix
- **Transitive dependency depth**: analysis and risk

---

## Dependency Evaluation Rubric

Before adding a new dependency, evaluate it against these criteria. Score each 1-5
(5 = best). Total score < 15 is high risk.

| Criteria | 5 (Best) | 3 (Acceptable) | 1 (High Risk) |
|----------|----------|---------------|---------------|
| **Maintenance** | Active commits in last month, multiple maintainers | Activity in last 6 months, single maintainer | No commits in >1 year |
| **Community** | >1000 stars, >100 contributors, active issue resolution | 100-1000 stars, issues get responses | <100 stars, issues ignored |
| **Release cadence** | Regular releases, clear changelog | Occasional releases, changelog exists | No releases in >1 year, no changelog |
| **Security history** | No known CVEs, security policy, private reporting | Minor CVEs with prompt fixes | Critical CVEs, no fix, no disclosure policy |
| **License** | MIT, Apache 2.0, BSD | LGPL, MPL (weak copyleft) | GPL, AGPL (strong copyleft), no license |
| **Dependencies of its own** | <5 transitive deps, all healthy | 5–20 transitive deps | >20 transitive deps, or depends on unmaintained packages |
| **Bus factor** | >3 active maintainers from different orgs | 1–2 maintainers | Single maintainer, no succession plan |
| **Documentation** | Comprehensive docs, examples, API reference | Basic README + API docs | Minimal or no documentation |

### Red flags that should block adoption
- No license file
- Unmaintained (no commits in >2 years)
- Known critical CVE without a fix
- Package name very similar to popular package (typosquatting indicator)
- Recently transferred to a new maintainer without explanation

---

## Version Pinning Strategy

### Exact pinning

```json
// package.json with exact versions
{ "dependencies": { "express": "4.18.2" } }

// requirements.txt with exact versions
express==4.18.2
```

**Pros:** Deterministic builds. Every developer and CI builds the same thing.
**Cons:** Must manually update versions. Can accumulate stale dependencies.

### Range pinning with lockfile

```json
// package.json with ranges
{ "dependencies": { "express": "^4.18.0" } }

// Lockfile (package-lock.json) pins exact versions of everything
```

**Pros:** `npm install` / `pip install` gets compatible updates within range.
Lockfile ensures reproducibility.
**Cons:** `npm install` without lockfile may get different versions on different machines.

### Recommendation

**Always commit lockfiles** (`package-lock.json`, `yarn.lock`, `Pipfile.lock`,
`Gemfile.lock`, `Cargo.lock`, `go.sum`). The lockfile is the source of truth
for what was actually tested and deployed. Ranges in the manifest express intent;
lockfiles express reality.

**For applications:** commit lockfiles. Deterministic builds matter more than
flexibility.
**For libraries:** use wide version ranges. Don't force consumers into specific
versions of transitive dependencies. Commit lockfiles for development, but
consumers use their own resolution.

---

## Supply Chain Security

### SLSA Framework (Supply-chain Levels for Software Artifacts)

| Level | Description | Requirements |
|-------|-------------|-------------|
| **SLSA 1** | Build is documented | Automated build process, provenance exists |
| **SLSA 2** | Tamper resistance via version control | Build service, signed provenance |
| **SLSA 3** | Hardened build platform | Non-falsifiable provenance, isolated builds, no user-defined build steps outside config |
| **SLSA 4** | Hermetic, reproducible, two-person review | All SLSA 3 + two-person review of all changes, hermetic builds, reproducible |

### Sigstore

Open-source project for signing and verifying software artifacts:
- **Cosign**: sign container images and other artifacts
- **Fulcio**: free code-signing certificates via OpenID Connect
- **Rekor**: transparency log for software supply chain

### Provenance

Provenance answers: who built this artifact, from what source, using what build
process, with what dependencies?

Tools:
- **npm**: `npm publish --provenance` (links package to its GitHub repo and build)
- **PyPI**: PEP 740 (attestations) for publishing signed provenance; use `pypi-attestations` tooling
- **Docker**: `docker build --provenance=true` (creates SLSA provenance)
- **SLSA GitHub Generator**: generates SLSA 3 provenance for GitHub Actions builds

### SBOM (Software Bill of Materials)

An SBOM lists every component in your software. It's essential for vulnerability
management: when Log4Shell hits, you need to know instantly whether you use Log4j.

**Formats:**
- **CycloneDX** (OWASP standard, XML/JSON) — most widely adopted
- **SPDX** (Linux Foundation standard, tag-value/JSON/YAML) — strong license tracking

**Tools:**
- **Syft**: generates SBOM from container images, filesystems, and packages
- **Trivy**: vulnerability scanner that also generates SBOMs
- **npm**: `npm sbom` (generates SPDX from package.json + lockfile)
- **pip**: `pip-audit` + `pipdeptree` for dependency tree

### Dependency scanning in CI

Every CI pipeline must run:

```
# npm (Node.js)
npm audit --audit-level=high

# pip (Python)
pip-audit

# Maven (Java)
mvn dependency-check:check

# Go
govulncheck ./...

# Rust
cargo audit

# GitHub Actions
- uses: github/codeql-action/upload-sarif
```

---

## License Compliance

### License type quick reference

| License | Type | Can use in commercial product? | Can modify? | Must share source? |
|---------|------|-------------------------------|-------------|-------------------|
| MIT | Permissive | Yes | Yes | No |
| Apache 2.0 | Permissive | Yes | Yes | No (patent grant) |
| BSD (2-clause, 3-clause) | Permissive | Yes | Yes | No |
| ISC | Permissive | Yes | Yes | No |
| MPL 2.0 | Weak copyleft | Yes (file-level) | Yes | Only modified MPL files |
| LGPL | Weak copyleft | Yes (library linking) | Yes | Only LGPL library changes |
| GPL 2.0 / 3.0 | Strong copyleft | **Risky** — may require entire product to be GPL | Yes | Yes — must share entire source |
| AGPL 3.0 | Strong copyleft (network) | **Very risky** — covers network use as distribution | Yes | Yes — even for SaaS |
| Unlicense / CC0 | Public domain | Yes | Yes | No |
| No license | Proprietary by default | **No** — no rights granted | **No** | N/A |

### Spec review application

Does the specification mandate license checks for dependencies? For SaaS products:
- GPL dependencies may be acceptable (you're not distributing the binary)
- AGPL dependencies are usually unacceptable (network use triggers the copyleft)
- A license scanning tool should be part of the CI pipeline

---

## Automated Dependency Management

### Dependabot / Renovate

Automatically open PRs for dependency updates.

**Configuration:**
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    allow:
      - dependency-type: "production"
```

**Best practices:**
- Group minor/patch updates into a single PR (Renovate is better at this)
- Security updates should be individual PRs (urgent, needs review)
- Require CI to pass before merging dependency PRs
- Set a PR limit to avoid notification fatigue

---

## Fork vs Wrap vs Replace Decision Matrix

| Situation | Action | Rationale |
|-----------|--------|-----------|
| Package unmaintained, small (<500 LOC) | Fork or vendor | Maintain internally; cost is low |
| Package unmaintained, large | Find alternative | Maintenance burden too high |
| Package maintained but has a bug | Contribute upstream + wrap workaround | Fix the source; wrap until upstream releases |
| Package API is unstable | Wrap behind your own interface | Insulate your code from API churn |
| Package is overkill for your use case | Find a smaller alternative or implement | Complexity cost > benefit |
| Package has GPL license | Replace with permissive alternative | Licensing risk |
| Package is critical + single maintainer | Evaluate bus factor; consider contributing | Mitigate the risk — become a contributor |

---

## Transitive Dependency Depth Analysis

A package with 3 direct dependencies might have 500 transitive dependencies.

**Risk:** Any of the 500 could introduce a vulnerability. Your update strategy must
account for transitive deps.

**Tools:**
```bash
# Visualize dependency tree
npm ls --depth=10
pipdeptree
cargo tree
mvn dependency:tree

# Count total dependencies
npm ls --depth=10 | wc -l
```

**Heuristics:**
- Total transitive dependency count >200: high risk
- Deepest chain >10 levels: high risk (too many links in the chain)
- A single package accounts for >20% of transitive deps: single point of failure

---

## Common Risks

- No lockfile committed → different developers and CI build with different dependency versions
- No dependency scanning in CI → known vulnerabilities deploy to production
- No license scanning → GPL/AGPL dependency slips into a commercial product
- No SCA (Software Composition Analysis) → Log4Shell-style incidents are undetectable
- "Works on my machine" because lockfile is not respected
- Dependabot/Renovate configured but PRs never reviewed → security updates pile up
- Adding a dependency when the standard library can do it (e.g., `left-pad` incident)
- Typosquatted package (e.g., `requests` vs `requessts`) added without verification

## Review questions

- Is the lockfile committed to version control?
- Is dependency scanning part of the CI pipeline? Are critical/high CVEs blocking?
- Is license compliance checking configured? Are copyleft licenses blocked if applicable?
- What is the total transitive dependency count for the primary package manager?
- Are there any unmaintained dependencies (no releases in >1 year)?
- Is there a policy for evaluating new dependencies before adding them?
- For critical runtime dependencies: what is the bus factor? Is there a fork plan?
- Are SBOMs generated and published with releases?
- Is artifact provenance (SLSA) configured for the build pipeline?
