# AI Security Review

Reviewed August 19, 2026 against the
[OWASP GenAI LLM Top 10 2026](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/)
as current guidance. This was a scoped review of GroundStack's implemented document-grounded
workflow; it is not a claim of complete compliance.

| Risk area | GroundStack control | Remaining limitation |
| --- | --- | --- |
| Prompt injection | Evidence is delimited as untrusted content; model output has no tool access | A model can still produce poor text |
| Sensitive information disclosure | Bounded excerpts, secret exclusions, no full prompt logging by default | Hosted providers receive selected excerpts |
| Supply chain | Locked JavaScript dependencies, Python audits, pinned CI actions, container builds | Dependency advisories change over time |
| Data and model poisoning | Only administrators can add approved documents | No automated provenance authority |
| Improper output handling | Markdown is rendered with controlled links; citations are validated | New renderers require review |
| Excessive agency | The model cannot execute tools or mutate external systems | Administrators can still upload harmful content |
| System prompt leakage | System prompts and secrets are server-side | Provider behavior is not a secrecy boundary |
| Vector and embedding weaknesses | Active-document filters, dimension checks, explicit distance threshold | Threshold requires corpus-specific evaluation |
| Misinformation | Unsupported questions abstain; source excerpts are inspectable | Citations reduce, but do not eliminate, hallucination |
| Unbounded consumption | Body, question, token, concurrency, and rate limits | Single-instance counters are not distributed |

Relevant tests cover prompt construction, fabricated citations, insufficient evidence,
authorization, URL safety, malformed files, and provider failures.
