# GroundStack Security Notes

## Source Text Is Untrusted

Retrieved chunks are wrapped as untrusted source content in the prompt. The system
prompt instructs the model to ignore commands found inside sources, never reveal
hidden prompts, and use source text only as evidence.

## Citation Guardrails

GroundStack does not trust generated citations. The answer is validated after model
output:

- accepted citations must match retrieved IDs such as `[S1]`
- fabricated IDs such as `[S99]` fail validation
- malformed IDs such as `[s1]` fail validation
- substantive answers without citations fail validation
- citations inside fenced code blocks are ignored

Failed validation triggers one repair attempt. If repair cannot produce a supported
answer, the assistant message is saved as failed rather than shown as grounded.

## URL Ingestion

URL ingestion remains allowlist-only and rejects credentials, redirects, private IP
ranges, unsupported content types, and oversized responses. Grounded generation does
not crawl external links found inside retrieved sources.

## Secrets

`.env.example` contains no secrets. `LLM_API_KEY` is used only for
OpenAI-compatible providers and should stay out of source control. Persisting rendered
prompts is controlled by `STORE_GENERATION_PROMPTS`; disable it if source context may
contain sensitive internal data.

## Authentication And Authorization

`APP_ENV` controls runtime behavior:

- `development` may use `DEV_AUTH_BYPASS_ENABLED=true` for local-only testing.
- `demo` may allow anonymous chat only when `ALLOW_ANONYMOUS_DEMO=true`.
- `production` fails startup validation if OIDC, exact CORS origins, trusted hosts,
  secure cookies, and metrics-token settings are incomplete.
- `test` rejects paid or remote model providers unless a test opts in explicitly.

Production authentication uses provider-neutral OIDC Authorization Code with PKCE.
The callback validates state, ID-token nonce, and the access token signature through
the issuer JWKS. Tokens must have a permitted algorithm, issuer, audience, `exp`,
`iat`, and `sub`; unsigned tokens are rejected.

Authorization is enforced in backend dependencies. Anonymous demo actors can ask
questions and submit feedback within strict limits. Source ingestion, evaluation,
training operations, observability detail, and model-configuration changes are admin
only. Conversation, message, and feedback queries are scoped by owner subject.

The knowledge base is still a shared admin-managed corpus. GroundStack is not yet a
fully isolated multi-tenant knowledge platform.

## Browser And API Hardening

The API enables trusted-host validation, exact credentialed CORS, security response
headers, request IDs, body-size checks, CSRF protection for cookie-authenticated unsafe
methods, sanitized error responses, and metrics-token protection. File ingestion also
checks extension, MIME type, file signature, and configured size limits.

## Discord Integration

Discord requests are accepted only through signed application-command interactions.
The `/integrations/discord/interactions` endpoint verifies the Ed25519 signature
against the exact raw body, validates timestamp freshness, deduplicates interaction
IDs, and returns safe Discord responses with `allowed_mentions` disabled. Retrieval
and generation run in a worker, not in the initial interaction window.

Discord tokens are encrypted while queued and cleared after delivery. User identity
is minimized to a keyed HMAC for ownership, rate limits, deletion, and feedback.
GroundStack does not require the Message Content intent, does not scan normal
messages, does not store usernames, and disables DMs by default.

Discord records are marked `source_platform=discord` and `training_eligible=false`.
The training-candidate API excludes them and rejects approval attempts, so Discord
feedback cannot silently become model-training data.

## Current Limits

OIDC sessions currently store the validated access token in an HttpOnly cookie rather
than a server-side session store. Logout clears the browser session; provider-side
revocation depends on the selected IdP. Production audit logging, PII redaction, and
tenant-isolated knowledge bases remain future work.
