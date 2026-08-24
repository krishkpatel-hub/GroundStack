# AI Security Review

Version: `1.0.0-rc.1`  
Review date: 2026-08-24

Current guidance checked: [OWASP GenAI LLM Top 10 2026](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/),
released August 3, 2026. Historical 2025 mappings are retained only for tests and controls that were
originally written against the 2025 category model.

This review is a release-candidate audit, not a certification or complete compliance claim.

## Findings

| Area | Status | Evidence |
| --- | --- | --- |
| Prompt injection | Mitigated | Prompt templates isolate instructions; retrieved text is evidence only; eval suite includes prompt-injection/security cases. |
| Citation spoofing | Mitigated | `validate_answer_citations` rejects missing, malformed, fabricated, or unsupported citations. |
| Unsupported answers | Mitigated | Empty evidence returns deterministic insufficient-evidence answer without LLM call. |
| System prompt disclosure | Partially mitigated | No route returns prompts; prompt persistence disabled by default. Provider sees prompts by design. |
| Sensitive data in outputs | Partially mitigated | No default private corpus; `.env` ignored; shared admin corpus means admins must not ingest private material into public demo. |
| Training data poisoning | Partially mitigated | Training candidates require human review; Discord data is never training eligible. |
| Excessive agency | Mitigated | LLM has no tool-calling authority or external side effects. |
| Discord abuse | Mitigated | Slash commands only, no Message Content intent, Ed25519 signature verification, replay protection, HMAC user IDs. |
| Unbounded consumption | Partially mitigated | Max question/body sizes, demo limits, provider concurrency, load profile safety gates. |
| Provider failure handling | Partially mitigated | Provider errors become visible failed messages; hosted-provider load tests require explicit opt-in. |

## Regression Tests

- `apps/api/tests/generation/test_grounding.py`
- `apps/api/tests/generation/test_fake_provider.py`
- `apps/api/tests/discord/test_security.py`
- `apps/api/tests/discord/test_replay.py`
- `apps/api/tests/discord/test_training_exclusion.py`
- `apps/api/tests/ingestion/test_url_security.py`
- `evaluation/runners/run_eval.py --suite all`

These tests cover concrete GroundStack controls and preserve earlier 2025-category mappings where
applicable. They do not prove complete coverage of every 2026 OWASP GenAI LLM risk.

## Release Decision

No P0 or P1 AI-security release blocker was identified in the local audit. The most important
deferred risk is tenant isolation: GroundStack has a shared admin-managed knowledge base, so it
should not be marketed as a multi-tenant product without additional authorization boundaries.
