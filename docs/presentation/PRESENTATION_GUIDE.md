# GroundStack Presentation Guide

GroundStack answers questions from approved documents and shows the source passages behind
each supported answer. It is a portfolio project, with no claimed customers or production usage.

## Start And Stop

From the repository root:

```bash
make dev
```

Open http://localhost:3000. This starts PostgreSQL, applies migrations, and starts FastAPI and
Next.js. Stop the foreground API and web processes with Ctrl+C, then run `make db-down` to stop
PostgreSQL without deleting its data. The application never seeds documents on startup.

## Configure A Real Model Privately

The local default is Ollama with `llama3.2:3b`. Install and start Ollama and install that model
before presenting, or configure an approved OpenAI-compatible provider in the root `.env`:

```dotenv
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://YOUR_PROVIDER_HOST
LLM_MODEL=YOUR_APPROVED_MODEL
LLM_API_KEY=ENTER_PRIVATELY
```

The base URL excludes `/v1`; the application appends it. Enter credentials only in `.env`,
never in chat or `NEXT_PUBLIC_*` variables. Restart the API after changing configuration.
This safe check reports presence only:

```bash
cd apps/api
.venv/bin/python -c 'from app.core.settings import get_settings; print("key configured:", bool(get_settings().llm_api_key))'
```

Check **Health** for provider availability. API readiness currently checks database readiness
in local development; it is not proof that a language model is available.

## Presentation Sequence

1. Start with empty Documents and Conversations. Explain the landing animation is illustrative.
2. Upload your own approved document through Documents. Text-based PDF, Markdown, plain text,
   and HTML are accepted up to 10 MB.
3. Observe Processing, wait for Ready, and inspect the extracted source excerpts.
4. Ask a precise question answered in that document. Check the answer and open every citation.
5. Ask about a topic absent from the document and confirm insufficient evidence.
6. Reload the page and confirm conversation persistence. Submit feedback and start a new chat.
7. Remove temporary validation material afterward. Document deletion removes chunks and
   embeddings. Conversation deletion archives history, so an isolated test database is required
   for automated database tests and disposal of their associated records.

Do not present mocked browser output or deterministic test-provider output as a real model result.
If provider setup is incomplete, disclose that grounded generation remains unverified.

## Trust And Limits

The architecture is Next.js, FastAPI, PostgreSQL/pgvector, an embedding model, and one generation
provider. Retrieved excerpts guide generation; citation validation rejects unknown source IDs.
Valid IDs alone do not prove every claim is correct, so inspect the source text.

Privacy depends on deployment, access control, retention, and provider handling. A hosted provider
may receive retrieved excerpts. Local development uses a development-only administrator identity;
it is not production authentication. Scanned PDFs need OCR, which is not included. Processing jobs
run inside the API process; after refresh, reselect a failed file to retry ingestion safely.

## Recovery

- API unavailable: use Retry connection after starting the stack with `make dev`.
- Provider unavailable: configure or start the selected provider, then retry the preserved question.
- Processing failed: use Retry processing while the file remains selected, or reselect the file.
- No evidence: inspect the document and ask a question it actually supports.
- Verify services with `docker compose ps`, `make migration-check`, and
  `curl --fail http://localhost:8000/api/v1/health/ready`.

Before presenting, finish a real-provider question with valid citations. Keep credentials and
private documents out of browser tabs, screenshots, and terminal output.
