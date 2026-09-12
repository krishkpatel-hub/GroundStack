# Security Policy

GroundStack `1.0.0-rc.1` is a release candidate for review. It is not a production service and no
public deployment is claimed.

## Reporting

Report suspected vulnerabilities privately to the repository owner. Do not open public issues for:

- Secrets or credentials.
- Authentication or authorization bypasses.
- Prompt-injection paths involving private data.
- Deployment or infrastructure weaknesses.

Never include access tokens, cookies, API keys, source documents, private prompts, or real user data
in reports.

## Supported Security Boundaries

- Provider-neutral OIDC and demo-mode auth boundaries.
- Admin-only document ingestion, source inspection, deletion, and settings routes.
- Scoped conversation and feedback ownership.
- Prompt-injection and citation-validation controls.
- Strict URL ingestion allowlist and private-IP rejection.
- Exact CORS/trusted-host requirements in demo/production modes.

## Known Limits

GroundStack is not yet a fully isolated multi-tenant knowledge platform. See
`docs/KNOWN_LIMITATIONS.md`, `docs/security/THREAT_MODEL.md`, and
`docs/security/AI_SECURITY_REVIEW.md`.

## Recommended GitHub Settings

The repository owner should enable:

- Secret scanning and push protection.
- Dependabot alerts and security updates.
- Dependency review for pull requests.
- CodeQL or equivalent code scanning.
- Branch protection requiring CI on `main`.

These settings require repository-owner permissions and are not changed by this release branch.
