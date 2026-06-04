import sys
import json
import re

VALID_SEVERITIES = {"low", "medium", "high", "critical"}

SEVERITY_RANK = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}

LIKELIHOOD_BY_SEVERITY = {
    "low": "low",
    "medium": "medium",
    "high": "high",
    "critical": "high",
}

SECURITY_TERMS = [
    "security", "authentication", "authorization", "permission",
    "access control", "encrypt", "owasp", "vulnerability", "credential",
    "authn", "authz", "jwt", "oauth", "openid", "saml",
    "csrf", "xss", "rbac", "iam", "tls", "ssl", "sql injection",
    "pki", "hmac", "signing", "token", "rate limit",
]

PERFORMANCE_TERMS = [
    "performance", "latency", "throughput", "scalability",
    "response time", "p95", "p99", "rps", "tps",
    "benchmark", "profiling", "load test", "stress test",
    "capacity", "slo", "sla",
]

DEVOPS_TERMS = [
    "ci/cd", "deployment", "rollback", "monitoring",
    "observability", "logging", "alerting", "pipeline",
    "infrastructure", "container", "kubernetes", "docker",
    "terraform", "health check", "probe",
]

DOCUMENTATION_TERMS = [
    "readme", "changelog", "api documentation", "api doc",
    "runbook", "adr", "architecture decision",
    "documentation", "docs",
]

VALID_CATEGORIES = {
    "spec", "business_logic", "architecture", "performance", "security",
    "testing", "devops", "dependencies", "standards", "ux",
    "documentation", "code_quality", "maintainability",
}


def _normalize_text(text):
    return re.sub(r"[-_\s]+", " ", text).lower().strip()


def _any_term_present(text, terms):
    norm_text = _normalize_text(text)
    for term in terms:
        norm_term = _normalize_text(term)
        pattern = r"\b" + re.escape(norm_term) + r"\b"
        if re.search(pattern, norm_text):
            return True
    return False


def load_spec(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: spec file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"Error: unable to read spec file {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def create_issue(title, severity, category, description, recommendation, evidence, impact):
    if severity not in VALID_SEVERITIES:
        raise ValueError(f"Invalid severity '{severity}'; expected one of {sorted(VALID_SEVERITIES)}")
    if category not in VALID_CATEGORIES:
        raise ValueError(f"Invalid category '{category}'; expected one of {sorted(VALID_CATEGORIES)}")
    return {
        "title": title,
        "severity": severity,
        "category": category,
        "description": description,
        "impact": impact,
        "evidence": evidence,
        "source_section": "automated_preflight",
        "recommendation": recommendation,
    }


def basic_analysis(spec):
    issues = []

    markers = re.findall(r'\b(TODO|FIXME|HACK)\b', spec, re.IGNORECASE)
    if markers:
        unique = sorted(set(m.upper() for m in markers))
        markers_str = ", ".join(unique)
        issues.append(create_issue(
            "Unresolved markers in specification",
            "medium",
            "spec",
            f"Specification contains unresolved markers: {markers_str}.",
            "Resolve all TODO/FIXME/HACK markers before implementation.",
            f"Found markers in the specification text: {markers_str}.",
            "Open markers usually indicate incomplete requirements or unresolved design decisions.",
        ))

    stripped = spec.strip()
    if len(stripped) < 50:
        issues.append(create_issue(
            "Specification too short",
            "high",
            "spec",
            "Specification lacks enough detail for a reliable engineering review.",
            "Expand the specification with functional, technical, and operational details.",
            f"Specification is {len(stripped)} characters (excluding leading/trailing whitespace).",
            "A specification this short is likely missing business rules, edge cases, or delivery constraints.",
        ))

    return issues


def detect_testing_gaps(spec):
    gaps = []
    norm_spec = _normalize_text(spec)

    if not re.search(r'\btest(?:s|ing|ed|able|er)?\b', norm_spec):
        gaps.append(create_issue(
            "No testing strategy defined",
            "high",
            "testing",
            "Specification does not mention a testing strategy.",
            "Define unit, integration, contract, and end-to-end testing expectations.",
            "No testing-related terms were found in the specification text.",
            "Missing test guidance makes implementation quality and release safety hard to evaluate.",
        ))

    if re.search(r'\be2e\b', norm_spec) and not re.search(r'\bunit[\s_-]?test(?:s|ing|ed|able|er)?\b', norm_spec):
        gaps.append(create_issue(
            "Imbalanced test strategy",
            "medium",
            "testing",
            "Specification mentions E2E tests without describing unit-test coverage.",
            "Follow a test-pyramid approach and define unit coverage for critical logic.",
            'Found "e2e" in the specification text but no occurrence of "unit test".',
            "Over-reliance on E2E tests usually slows feedback and leaves core logic under-specified.",
        ))

    return gaps


def detect_security_gaps(spec):
    gaps = []

    if not _any_term_present(spec, SECURITY_TERMS):
        gaps.append(create_issue(
            "No security considerations mentioned",
            "high",
            "security",
            "Specification does not mention security, authentication, authorization, or access control.",
            "Define security boundaries, authentication requirements, and data protection expectations.",
            "No security-related terms were found in the specification text.",
            "Missing security guidance increases the risk of insecure design and missed threat vectors.",
        ))

    return gaps


def detect_performance_gaps(spec):
    gaps = []

    if not _any_term_present(spec, PERFORMANCE_TERMS):
        gaps.append(create_issue(
            "No performance requirements mentioned",
            "medium",
            "performance",
            "Specification does not mention performance, latency, throughput, or scalability expectations.",
            "Define performance targets, SLOs, or acceptance criteria for latency-sensitive operations.",
            "No performance-related terms were found in the specification text.",
            "Missing performance guidance may lead to designs that do not meet user or operational expectations.",
        ))

    return gaps


def detect_devops_gaps(spec):
    gaps = []

    if not _any_term_present(spec, DEVOPS_TERMS):
        gaps.append(create_issue(
            "No DevOps or deployment strategy mentioned",
            "medium",
            "devops",
            "Specification does not mention CI/CD, deployment, monitoring, or observability.",
            "Define deployment strategy, CI pipeline, rollback plan, and operational monitoring approach.",
            "No DevOps-related terms were found in the specification text.",
            "Missing DevOps guidance may lead to unreliable deployments and poor operational visibility.",
        ))

    return gaps


def detect_documentation_gaps(spec):
    gaps = []

    if not _any_term_present(spec, DOCUMENTATION_TERMS):
        gaps.append(create_issue(
            "No documentation plan mentioned",
            "low",
            "documentation",
            "Specification does not mention documentation, README, changelog, or runbook expectations.",
            "Define documentation requirements: README, API docs, changelog, runbooks, and ADRs.",
            "No documentation-related terms were found in the specification text.",
            "Missing documentation expectations can lead to operational confusion and slower onboarding.",
        ))

    return gaps


def build_summary(issues):
    if any(issue["severity"] in {"high", "critical"} for issue in issues):
        verdict = "not_ready"
    elif issues:
        verdict = "ready_with_risks"
    else:
        verdict = "ready"

    return {
        "system_goal": None,
        "scope": "Automated preflight based on lightweight text heuristics.",
        "verdict": verdict,
        "top_risks": [
            issue["title"]
            for issue in sorted(
                issues,
                key=lambda i: SEVERITY_RANK[i["severity"]],
                reverse=True,
            )[:3]
        ],
        "missing_information": [],
        "assumptions": [
            "This helper performs shallow text checks and does not replace the full ai-spec-review skill contract."
        ],
    }


def build_risk_register(issues):
    risk_register = []

    sorted_issues = sorted(
        issues,
        key=lambda i: SEVERITY_RANK[i["severity"]],
        reverse=True,
    )

    for index, issue in enumerate(sorted_issues, start=1):
        risk_register.append({
            "id": f"risk-{index}",
            "title": issue["title"],
            "severity": issue["severity"],
            "likelihood": LIKELIHOOD_BY_SEVERITY[issue["severity"]],
            "category": issue["category"],
            "affected_area": "specification",
            "trigger": issue["description"],
            "mitigation": issue["recommendation"],
            "owner": "spec_author",
        })

    return risk_register


def main():
    if len(sys.argv) < 2:
        print("Usage: review_spec.py <spec.md>", file=sys.stderr)
        sys.exit(1)

    spec = load_spec(sys.argv[1])
    issues = (
        basic_analysis(spec)
        + detect_testing_gaps(spec)
        + detect_security_gaps(spec)
        + detect_performance_gaps(spec)
        + detect_devops_gaps(spec)
        + detect_documentation_gaps(spec)
    )

    result = {
        "summary": build_summary(issues),
        "risk_register": build_risk_register(issues),
        "issues": issues,
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
