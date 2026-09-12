# Presentation Quality Review

Reviewed September 12, 2026, on `fix/presentation-ready-e2e`.

**Presentation-ready: not yet.** The remaining core-workflow blocker is private owner
configuration of a working generation provider. No real generated answer or its citations
were verified. Automated responses are not evidence of real-provider success.

## Local State

- URL: http://localhost:3000; start from the repository root with `make dev`.
- Stop API and Next.js with Ctrl+C, then `make db-down`. Database volumes are retained.
- PostgreSQL 17 is healthy; pgvector is 0.8.6; migration head is `202608220001`.
- `/api/v1/health/live` and `/api/v1/health/ready` succeed. Local readiness checks the
  database, not generation-provider availability.
- The configured presentation database is empty: sources, documents, chunks, jobs,
  conversations, messages, citations, feedback, generation runs, retrieval runs, and
  retrieval results all contain zero rows after cleanup and application restart.
- No temporary validation file remains. The application does not seed data on startup.
- An older, inactive database was preserved because record ownership was not sufficiently
  established for irreversible deletion. It is not the database used by this workspace.

## Real Browser Workflow

| Check                                           | Result                                                             |
| ----------------------------------------------- | ------------------------------------------------------------------ |
| Empty workspace, actual file chooser upload     | Passed with an original neutral temporary text file                |
| Processing, Ready, stored excerpt               | Passed with real extraction, embeddings, and PostgreSQL storage    |
| Duplicate upload                                | Already imported; no extra document or chunk                       |
| Supported question retrieval                    | Correct chunk selected; cosine distance 0.21875                    |
| Real generation and expanded generated citation | Blocked: configured Ollama model unavailable                       |
| Unsupported question                            | Insufficient evidence; no general-knowledge answer                 |
| Conversation reload and feedback                | Refusal and saved Helpful feedback survived reload                 |
| New chat                                        | Passed                                                             |
| Document deletion                               | Stored document, chunks, and embeddings removed                    |
| Temporary history and feedback cleanup          | Passed; targeted transaction followed by zero-row checks           |
| API outage and Retry connection                 | One alert; retry restores data and authorized navigation           |
| Authorization                                   | Ordinary development user receives 403 for document administration |
| Console after restoring services                | No warnings/errors observed on the final workspace navigation      |

Live tests used the actual API, database, and embedding model. They did not substitute a
deterministic generation provider. The configured provider is Ollama, model `llama3.2:3b`;
neither Ollama nor that model is installed locally. No large model was downloaded.

## Automated Verification

| Check                                                  | Result                                                                                                     |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| API suite                                              | 46 passed, including authorization, ingestion, retrieval, citation validation, refusal, and recovery tests |
| Isolated PostgreSQL lifecycle test                     | Passed: failed embedding rollback, retry, deduplication, deletion; temporary database removed              |
| PostgreSQL backup/restore                              | Passed using PostgreSQL 17 utilities in the running container                                              |
| Ruff format/lint and Python compilation                | Passed                                                                                                     |
| Migration graph and Alembic schema check               | Passed; no new upgrade operations detected                                                                 |
| Frontend unit tests                                    | 5 passed                                                                                                   |
| Playwright suite                                       | 96 passed across Chromium, Firefox, WebKit, and mobile Chromium                                            |
| Final excerpt-recovery regression rerun                | 4 passed after adding stale-error dismissal                                                                |
| Frontend formatting, lint, typecheck, production build | Passed                                                                                                     |
| Accessibility and reduced motion                       | Existing axe, keyboard/dialog, navigation, and reduced-motion browser tests passed                         |
| Responsive overflow                                    | Six routes at 320, 375, 430, 768, 1024, 1280, and 1440 pixels passed                                       |
| Zoom                                                   | 200% CSS-zoom equivalent passed; physical browser zoom not independently verified                          |
| Bundle budget                                          | Passed: 28 assets, 1,192,680 bytes                                                                         |
| Docker                                                 | API/frontend image builds and Compose configuration passed                                                 |
| Dependency audits                                      | npm and pip audits found no known dependency vulnerabilities                                               |
| Repository scanner and self-test                       | Passed; scanner checks selected credential patterns, not a formal security guarantee                       |

The browser suite uses isolated intercepted API responses. The database lifecycle test
uses real PostgreSQL with deterministic embeddings. Neither proves real model answer
quality. The editable local API package is not published on PyPI and cannot itself be
audited there. Local pip was updated before rerunning its audit; no dependency manifest
was changed for that environment-only update.

Native scrolling was exercised in the browser and the existing passive-scroll behavior
was retained. No wheel interception or mandatory scroll snapping is used. Physical
MacBook momentum/gesture feel is an owner check, not an automated pass.

## Product And File Changes

The existing shared system font is retained without a remote font request. Shared colors
remain navy `#07142f`, blue `#246bfd`, teal `#43b8ba`, canvas `#f7f9fc`, white, ink
`#101828`, secondary text `#536174`, border `#dce3ee`, and selected state `#eaf1ff`.
The landing animation remains a pausable, reduced-motion-aware conceptual illustration.
The workspace has less repeated copy and empty vertical space; no architecture redesign.

| Files                                                                                                      | Why                                                                                                                                            |
| ---------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/web/components/app-shell.tsx`                                                                        | Remove canned questions/repeated copy; prevent stale conversation and stream updates; preserve failed drafts; handle history mutation errors   |
| `apps/web/components/knowledge/knowledge-base.tsx`                                                         | Guard repeated submissions, preserve partial upload success, retry failed processing/excerpts, show full excerpts, correct deletion pagination |
| `apps/web/components/api-connection-alert.tsx`                                                             | Notify navigation when connection recovery is requested                                                                                        |
| `apps/web/components/app-frame.tsx`, `apps/web/components/workspace-nav.tsx`                               | Refresh existing authentication state on Retry connection                                                                                      |
| `apps/web/lib/api.ts`                                                                                      | Share the recovery event name                                                                                                                  |
| `apps/web/lib/knowledge.ts`                                                                                | Reject empty uploads before network submission                                                                                                 |
| `apps/web/components/landing-experience.tsx`                                                               | Replace named fictional files/error code with generic illustrative content                                                                     |
| `apps/web/app/globals.css`                                                                                 | Remove unused suggestion/banner styles and oversized empty chat minimum heights                                                                |
| `apps/web/tests/e2e/product.spec.ts`                                                                       | Neutral isolated fixtures; six new recovery/race/input tests, repeated across four browser projects                                            |
| `apps/api/app/models/knowledge.py`, `apps/api/app/models/conversation.py`                                  | Match index metadata already present in migrations; no physical schema change                                                                  |
| `apps/api/migrations/env.py`                                                                               | Reflect pgvector dimensions during schema validation                                                                                           |
| `apps/api/tests/ingestion/test_database_lifecycle.py`                                                      | Add isolated real-database lifecycle coverage                                                                                                  |
| `apps/api/tests/api/test_documents.py`                                                                     | Make the intended administrator identity explicit in the 404 test                                                                              |
| `apps/api/tests/api/test_conversation_messages.py`, `apps/api/tests/retrieval/test_query_and_selection.py` | Remove old presentation-specific fixture labels                                                                                                |
| `README.md`, `docs/PRIVACY_AND_DATA_GOVERNANCE.md`                                                         | Remove bundled-demo claims; preserve honest privacy limits                                                                                     |
| `docs/presentation/PRESENTATION_GUIDE.md`                                                                  | Document empty startup, private provider configuration, honest presentation flow and recovery                                                  |
| `docs/presentation/QUALITY_REVIEW.md`                                                                      | Record verification scope and blockers                                                                                                         |
| Deleted `docs/presentation/groundstack-presentation-validation.md`                                         | Remove bundled presentation document                                                                                                           |
| Deleted `docs/assets/screenshots/workspace-{ask,citation,documents,mobile}.png`                            | Remove screenshots populated with mocked presentation records                                                                                  |

Authentication enforcement, API contracts, retrieval algorithms, provider integration,
and production deployment configuration were not changed.

## Before Presenting

1. Install/start the configured Ollama provider and obtain `llama3.2:3b`, or privately
   configure an approved hosted provider using `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_MODEL`,
   and `LLM_API_KEY` in the repository-root `.env`. Never paste a key into chat.
2. Restart the API, upload an approved document, ask a supported question, and inspect
   every generated citation. This remains the one blocked end-to-end step.
3. Check physical trackpad feel and actual 200% browser zoom on the presentation machine.

The [presentation guide](PRESENTATION_GUIDE.md) includes a secret-presence-only command.
Hosted providers may receive retrieved excerpts. Citation-ID validation does not establish
claim-level truth. Failed processing can be retried from the selected file; after refresh
the file must be selected again. Jobs are process-local. Conversation deletion archives
history rather than purging it. No real customer or production adoption is claimed.
