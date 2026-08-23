# GroundStack Threat Model

Version: `1.0.0-rc.1`  
Guidance checked: OWASP GenAI LLM Top 10 2026, published August 4, 2026, plus the
OWASP GenAI/LLM Top 10 2025 category model still referenced by industry mappings.

## Assets

- Source documents, chunks, embeddings, retrieval diagnostics, conversations, generated answers,
  feedback, evaluation records, training candidates, Discord records, OIDC/session data, provider
  credentials, database credentials, Redis credentials, and deployment configuration.

## Trust Boundaries

- Browser to API.
- Anonymous demo actor to authenticated/admin actor.
- Admin ingestion inputs to parser/chunker/embedding store.
- Retrieved source text to LLM prompt.
- API to LLM/embedding/reranking providers.
- Discord signed interaction endpoint to internal queue/worker.
- CI/deployment secret stores to runtime containers.

## Risk Register

| Risk | Status | Controls | Residual risk |
| --- | --- | --- | --- |
| Direct prompt injection | Mitigated | Grounded prompt template, citation validation, insufficient-evidence behavior, security evals | Model may still produce low-quality text that must be rejected by validation. |
| Indirect prompt injection through retrieved docs | Partially mitigated | Source text treated as untrusted, no tool execution from model output, citation validation | More adversarial eval coverage is future work. |
| Sensitive information disclosure | Partially mitigated | Server-only env vars, no prompt persistence by default, scoped conversations, metrics-token protection | Admin-ingested private docs are still retrievable to authorized app users because corpus is shared. |
| Supply-chain compromise | Partially mitigated | Lockfiles, pinned GitHub Actions, Dependabot, CI dependency checks | Local vulnerability tooling may require network access; owner must enable GitHub security settings. |
| Data/model poisoning | Partially mitigated | Admin-only ingestion, provenance metadata, training-candidate human review | No automated malicious-document classifier. |
| Improper output handling | Mitigated | Markdown rendering in web UI, Discord markdown sanitization, allowed mentions disabled | Future rich renderers need review. |
| Excessive agency | Mitigated | LLM cannot call tools or mutate systems; Discord uses explicit slash commands only | None beyond normal API authorization risk. |
| System prompt leakage | Partially mitigated | Prompt is not returned by APIs; prompt injection tests cover hidden-instruction disclosure | A compromised provider could observe prompts. |
| Vector/embedding authorization weakness | Partially mitigated | Admin-managed shared corpus; conversations scoped by owner | Not tenant-isolated. |
| Misinformation/unsupported answers | Mitigated | Retrieved evidence required, citation validation and repair, deterministic abstention | Evaluation set is finite. |
| Unbounded consumption | Partially mitigated | Demo limits, provider concurrency, Discord limits, fake load profiles, max body/question sizes | Full staging load evidence is not yet available. |
| SSRF and unsafe URLs | Mitigated | URL allowlist, scheme checks, private IP rejection, no crawling | DNS rebinding should remain covered by tests. |
| Discord signature/replay abuse | Mitigated | Raw-body Ed25519 verification, timestamp check, Redis replay claim, DB dedupe fallback | Live Discord sandbox not yet executed. |
| Secret exposure | Partially mitigated | `.gitignore`, placeholder env examples, secret scans, no frontend server secret usage | Public git history must be monitored; no history rewrite performed. |

## Accepted Limitations

GroundStack `1.0.0-rc.1` is a portfolio-grade release candidate, not a production SaaS service.
Residual risks that require product decisions or infrastructure ownership are tracked in
`docs/KNOWN_LIMITATIONS.md` and `docs/ROADMAP.md`.
