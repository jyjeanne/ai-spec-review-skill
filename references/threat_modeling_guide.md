# Threat Modeling Guide

## Focus areas

- **STRIDE methodology**: threat categories per component type
- **Attack trees**: decomposing attack scenarios
- **Trust boundary mapping**: identifying where trust levels change
- **Kill chain phases**: controls at each attack phase
- **Threat prioritization**: DREAD and CVSS scoring
- **Spec review integration**: applying threat modeling in the review process

---

## STRIDE Methodology

Classify threats using STRIDE categories. For each component in the system, ask what
could go wrong in each category:

| Category | Threat | Example |
|----------|--------|---------|
| **S**poofing | Pretending to be someone/something else | Using stolen credentials, forging JWT, IP spoofing |
| **T**ampering | Modifying data or code without authorization | SQL injection altering data, MITM modifying API responses |
| **R**epudiation | Denying having performed an action | User denies placing order; no audit trail proves they did |
| **I**nformation Disclosure | Exposing information to unauthorized parties | API returns other users' data, error messages leak DB schema |
| **D**enial of Service | Making the system unavailable | DDoS, resource exhaustion, algorithmic complexity attacks |
| **E**levation of Privilege | Gaining higher access than authorized | Horizontal (access other user's data) or vertical (gain admin) |

### STRIDE by component type

| Component type | Primary threats |
|---------------|----------------|
| Web application | Spoofing (auth), Tampering (input validation), Info Disclosure (error handling) |
| API server | Spoofing (JWT), Elevation of Privilege (BOLA/IDOR), DoS (rate limiting) |
| Database | Tampering (SQLi), Info Disclosure (direct access), Repudiation (no audit log) |
| Message queue | Tampering (message content), Info Disclosure (message payload), Repudiation (no trace) |
| File storage | Tampering (file content), Info Disclosure (public bucket), DoS (large file upload) |
| Mobile client | Tampering (client-side logic), Info Disclosure (local storage), Spoofing (device ID) |
| CI/CD pipeline | Tampering (supply chain), Elevation of Privilege (pipeline credentials), DoS |

### Spec review application

For each component implied by the specification:
1. List its STRIDE threats
2. Check if the spec addresses each threat
3. Flag unaddressed threats as security issues with OWASP category mapping

---

## Attack Trees

Decompose an attack goal into its OR and AND subgoals.

### Example: "Gain unauthorized access to user account"

```
Gain unauthorized access to user account
├── OR
│   ├── Steal credentials
│   │   ├── OR
│   │   │   ├── Phish user (social engineering)
│   │   │   ├── Credential stuffing (reuse from breached site)
│   │   │   └── Brute force (no rate limiting on login)
│   │
│   ├── Bypass authentication
│   │   ├── OR
│   │   │   ├── Forge JWT (weak signing key, algorithm confusion)
│   │   │   ├── Session fixation / hijacking
│   │   │   └── Exploit auth logic flaw
│   │
│   └── Password reset flow abuse
│       ├── OR
│       │   ├── Enumerate users via reset (difference in response)
│       │   ├── Guess reset token (weak randomness)
│       │   └── Intercept reset email (email not TLS-encrypted)
```

### Spec review application

Build attack trees for critical security properties: authentication, authorization,
data protection, payment integrity. Check whether the spec's controls block every
leaf node.

---

## Trust Boundary Mapping

### What is a trust boundary?

A trust boundary is any point where data passes between components with different
trust levels. Data crossing a trust boundary must be validated, authenticated, or
authorized — you cannot trust it.

### Trust boundaries in typical architectures

| Boundary | Example | Controls needed |
|----------|---------|----------------|
| User ↔ Web server | HTTP request from browser | Input validation, CSRF token, auth check |
| Web server ↔ API | Internal HTTP/gRPC | Service-to-service auth, TLS mutual auth |
| API ↔ Database | SQL query | Parameterized queries, least-privilege DB user |
| API ↔ External service | Third-party API call | API key management, timeout, circuit breaker |
| API ↔ Message queue | Publish message | Message signing, schema validation |
| CI ↔ Production | Deploy artifact | Signed artifacts, provenance verification |

### Spec review application

Draw the system context diagram. Mark trust boundaries. For each boundary crossing:
- Is data validated as it crosses?
- Is the caller authenticated and authorized?
- Is the communication encrypted?
- Are the components on each side at different trust levels? If so, what controls exist?

---

## Kill Chain and Defense in Depth

### Kill chain phases (adapted from Lockheed Martin Cyber Kill Chain)

| Phase | Description | Controls |
|-------|-------------|----------|
| 1. Reconnaissance | Attacker gathers information | Rate limiting, minimal info in errors, no verbose headers |
| 2. Weaponization | Attacker creates exploit | Not directly controllable |
| 3. Delivery | Exploit reaches the system | Input validation, WAF, CSP headers |
| 4. Exploitation | Vulnerability triggered | Input sanitization, parameterized queries, memory safety |
| 5. Installation | Attacker establishes persistence | Least privilege, read-only filesystem, immutable infrastructure |
| 6. Command & Control | Attacker remote controls system | Egress filtering, network monitoring, anomaly detection |
| 7. Actions on Objective | Attacker achieves goal | Data encryption, audit logging, anomaly detection |

**Defense in depth principle:** Every phase should have controls. If phase 3 fails
(e.g., an XSS payload reaches the server), phase 4 should still block it (output encoding).
If phase 4 fails, phase 5 should limit the damage (least privilege, no exec).

### Spec review application

For each STRIDE threat identified, trace it through the kill chain. Does the spec
have controls at multiple phases, or does it rely on a single point of failure?

---

## Threat Prioritization

### DREAD model

Score each threat 1-10 in each category:

| Category | Question |
|----------|----------|
| **D**amage potential | How severe would the impact be? (data loss, financial, reputational) |
| **R**eproducibility | How easy is the attack to reproduce? (always, sometimes, rare conditions) |
| **E**xploitability | How easy is it to launch the attack? (script kiddie, expert, nation-state) |
| **A**ffected users | What percentage of users are affected? (all, many, few) |
| **D**iscoverability | How easy is the vulnerability to discover? (public knowledge, documented, obscure) |

**Score:** Sum or average the 5 ratings. Higher = higher priority.

### CVSS (Common Vulnerability Scoring System)

Industry-standard numeric score (0-10). Factors: attack vector, complexity, privileges
required, user interaction, scope, confidentiality/integrity/availability impact.

**Severity bands:**
- 0.0 — None
- 0.1–3.9 — Low
- 4.0–6.9 — Medium
- 7.0–8.9 — High
- 9.0–10.0 — Critical

### Spec review application

Prioritize findings by potential impact, not by ease of discovery. A critical
vulnerability that's hard to exploit is still critical — attackers are resourceful.

---

## Security Review Checklists by Architecture

### Monolith

- [ ] All user input validated at entry points
- [ ] CSRF tokens on state-changing requests
- [ ] Session management (HTTP-only, Secure, SameSite cookies)
- [ ] SQL injection: all queries parameterized
- [ ] File upload: type validation, size limits, virus scanning, storage outside webroot
- [ ] Admin endpoints: separate auth, IP restriction, audit logging

### Microservices

- [ ] Service-to-service authentication (mTLS, JWT, SPIFFE)
- [ ] API gateway: auth, rate limiting, input validation at the edge
- [ ] No direct database access from external — always through service
- [ ] Secrets management: per-service credentials, not shared across services
- [ ] Network segmentation: services can only reach what they need
- [ ] Distributed tracing includes auth context for audit

### Serverless

- [ ] Function-level IAM roles (least privilege per function)
- [ ] No secrets in function environment variables (use Secrets Manager)
- [ ] Input validation at function entry (API Gateway can validate, but function
  must re-validate)
- [ ] Cold start data: global scope variables that persist across invocations —
  don't cache user-specific data
- [ ] Event source validation: verify the event came from the expected source

### Mobile API

- [ ] Certificate pinning (or at minimum, enforce HTTPS)
- [ ] No secrets in mobile binary (API keys, private keys — extractable)
- [ ] Token-based auth (not session cookies)
- [ ] Minimal data in local storage — encrypt sensitive local data
- [ ] Server-side validation of all client-submitted data (never trust the client)

---

## Common Risks

- Threat modeling skipped entirely — security considered "later"
- Single trust boundary assumption ("everything behind the firewall is safe")
- No consideration of insider threats (developer with DB access, CI pipeline compromise)
- STRIDE applied only to the UI layer, ignoring backend services and infrastructure
- No defense in depth — relying on a single control (firewall, WAF) for protection
- Threat prioritization based on ease rather than impact

## Review questions

- Has threat modeling been performed? If not, what are the top 5 STRIDE threats
  for the most critical component?
- Where are the trust boundaries in the proposed architecture?
- Are there controls at every layer, or does the spec rely on perimeter-only security?
- Are there insider threat vectors (CI pipeline, developer access, support tools)?
- Does the spec address repudiation threats (audit trails, non-repudiation)?
- For each critical business flow, what is the attack tree? Are all leaf nodes covered?
- Is defense-in-depth applied to the most critical assets?
