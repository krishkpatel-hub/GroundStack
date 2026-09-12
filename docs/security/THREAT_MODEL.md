# Threat Model

## Assets

Approved document text, embeddings, conversations, citations, feedback, identity/session data,
database credentials, and model-provider credentials.

## Trust Boundaries

- Browser to Next.js and FastAPI.
- FastAPI to PostgreSQL/pgvector.
- FastAPI to the configured embedding and generation providers.
- Administrator-controlled document content to the retrieval and generation pipeline.

## Primary Threats

| Threat | Control | Residual risk |
| --- | --- | --- |
| Unauthorized administration | Server-side admin dependency on every mutation route | Local development uses a simplified identity |
| Cross-user conversation access | Owner subject filters on conversation and feedback queries | Shared knowledge base is not tenant-isolated |
| Malicious upload | Type, size, content, extraction, and transaction checks | Text-based parsing is not malware scanning |
| Server-side URL request forgery | Host allowlist, DNS/IP checks, redirect and content limits | Network policy should also restrict egress |
| Prompt injection in documents | Untrusted evidence delimiters and no model tool access | Model output still requires user review |
| Fabricated evidence | Citation IDs checked against retrieved chunks | A valid excerpt may still be interpreted poorly |
| Data leakage | Bounded context, disabled query storage, redacted configuration | Hosted providers receive selected evidence |
| Resource exhaustion | Request, token, concurrency, and rate limits | Limits are process-local in one-instance mode |
| Secret exposure | Server-only variables, scanner, ignored local files | Owner dashboard configuration remains external |

The development configuration is suitable for a local portfolio demonstration, not a
production municipality deployment. A production pilot requires identity integration, data
classification, retention decisions, provider review, network controls, backup testing, and an
independent security review.
