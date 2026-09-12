# GroundStack Presentation Guide

## One-sentence explanation

GroundStack lets an organization upload approved documents, ask questions about them, and verify each supported answer against the cited source text.

## Problem

Organizations often spread policies, procedures, manuals, and technical knowledge across many documents. People lose time searching, and a plausible chatbot answer is not enough when the information must be accurate.

## Solution

An authorized administrator adds approved documents to GroundStack. A user asks a question, the application retrieves relevant passages, and a language model writes an answer using only that evidence. GroundStack displays the supporting excerpts and refuses when the documents do not contain enough information.

## Honest privacy explanation

Documents are stored in the infrastructure configured by the organization. The selected model provider determines whether retrieved excerpts are sent to an external service; a self-hosted model can reduce external exposure. Access control, secure deployment, retention rules, and provider agreements are still required. GroundStack is a portfolio project and has not been adopted by a real township or company.

## Simple architecture

User -> Next.js interface -> FastAPI backend -> PostgreSQL/pgvector -> relevant document sections -> language model -> citation validation -> answer

## Start and stop

From the repository root, start the complete local stack with:

```bash
make dev
```

Stop the API and web processes with `Ctrl+C`. When PostgreSQL is no longer
needed, stop it without deleting its data with `make db-down`.

## Exact live presentation sequence

1. Open `http://localhost:3000` and explain the problem in one sentence.
2. Select **Open workspace**, then open **Documents**.
3. Confirm the knowledge base is empty.
4. Upload `docs/presentation/groundstack-presentation-validation.md`.
5. Show the Processing state, wait for Ready, and expand its source excerpt.
6. Open **Ask** and submit the supported question below.
7. Open every citation and compare the excerpt with the document.
8. Submit the follow-up question.
9. Submit the unsupported question and show the insufficient-evidence response.
10. Refresh the browser and show that conversation history remains.
11. Mark the supported answer helpful, then start a new chat.
12. After presentation evidence is captured, delete the validation document and confirm the knowledge base is empty.
13. Close with the technology, limitations, and lessons learned.

## Prepared questions

Supported question:

> What does GS-DEMO-217 mean, and how should I resolve it?

Expected evidence: the **Error GS-DEMO-217** and **Resolution** sections. A supported answer should identify the stale configuration-revision mismatch, refresh configuration, restart only the validation worker, and verify `validation_status=ready` and `revision_match=true`.

Follow-up question:

> What should I do if the revisions still differ after one refresh?

Expected evidence: the final paragraph of **Resolution**, which says to stop retrying and ask the application owner to inspect the configuration publication log.

Unsupported question:

> What is the organization's parental-leave policy?

Expected behavior: GroundStack states that it lacks sufficient retrieved evidence and does not provide a general policy answer.

## Short speaking script

I built GroundStack because organizations often have useful procedures locked inside documents, but finding the right passage quickly can be difficult. GroundStack is a private-facing knowledge assistant: an authorized administrator uploads approved material, and users ask questions against that controlled knowledge base.

The main AI pattern is retrieval-augmented generation, or RAG. In simple terms, the application first searches the uploaded documents for relevant sections. It then gives those sections to the language model with instructions to answer only from that evidence. PostgreSQL stores the documents, conversations, and feedback, while pgvector stores numerical representations called embeddings that make meaning-based search possible.

The language model writes the response, but it does not decide which sources are valid. GroundStack tracks the retrieved document and chunk identifiers, checks citations against that evidence, and shows the exact excerpts to the user. If there is not enough evidence, it refuses instead of quietly using general model knowledge.

I built the Next.js and TypeScript interface, the FastAPI and Python backend, the ingestion and retrieval pipeline, the PostgreSQL models and migrations, the citation checks, and the automated tests. The biggest lesson was that a useful AI product is not just a prompt: data validation, authorization, failure handling, and honest limits matter just as much.

This is a portfolio project, not a production municipal system. Authentication is simplified for local development, privacy depends on the chosen deployment and model provider, and a real deployment would need an organization-specific security and governance review.

## Likely questions and honest answers

**Why not just use ChatGPT?** GroundStack limits answers to an approved document set and makes the supporting excerpts inspectable. General chat tools can be useful, but they do not automatically enforce this application's evidence boundary or document permissions.

**Are uploaded documents private?** Not automatically. They are stored in the configured database, and relevant excerpts may be sent to the configured model provider. Privacy depends on deployment, access control, logging, retention, and provider terms.

**What is RAG?** It means retrieving relevant source text before asking a model to write an answer.

**What are embeddings?** They are numerical representations of text that let the database compare passages by meaning rather than only exact words.

**Why PostgreSQL and pgvector?** They keep relational application data and vector search in one well-understood database for this project scale.

**What does the LLM actually do?** It turns retrieved evidence into a concise natural-language answer. It does not upload, authorize, retrieve, or validate citations.

**Can the system hallucinate?** Yes, language models can still make mistakes. GroundStack reduces that risk with evidence-only prompts, relevance checks, citation validation, and refusal behavior, but users should inspect sources.

**How are citations verified?** The backend accepts only citation identifiers tied to chunks retrieved for that question. Fabricated identifiers cause validation failure rather than a completed grounded answer.

**What happens when the answer is not in the documents?** GroundStack returns an insufficient-evidence response and does not call on general knowledge as a fallback.

**Who can upload documents?** The API requires an administrator identity. Local development uses an explicit development-only identity shortcut; production requires real authentication configuration.

**Could a municipality use this?** The concept could be adapted, but a real pilot would require security, privacy, records-retention, accessibility, procurement, and provider reviews.

**Is it currently production-deployed?** No. This presentation uses a local development deployment.

**What did you personally build?** I implemented and integrated the frontend, backend, database models and migrations, document pipeline, grounded-answer flow, citations, history, feedback, tests, and local tooling represented in this repository.

**What would you improve next?** I would conduct a deployment-specific threat review, add production identity integration, improve background job durability, and evaluate retrieval quality on an approved real-world test set.

**What are the main security limitations?** The local auth shortcut is not production authentication, uploaded content is untrusted, provider data handling varies, and operational controls require deployment-specific configuration and monitoring.

## Recovery checklist

- Docker not running: open Docker Desktop, wait until it reports ready, then run `make dev` again.
- Database not ready: run `docker compose ps postgres`; wait for `healthy`, then run `make migrate`.
- API not ready: run `curl -fsS http://localhost:8000/api/v1/health/ready`; restart with `make api-dev` if needed.
- Frontend not loading: run `npm run dev --workspace apps/web` and open `http://localhost:3000`.
- LLM key missing: set `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_MODEL`, and `LLM_API_KEY` privately in `.env`; confirm only that `LLM_API_KEY` is non-empty without printing it.
- Provider unavailable: keep the document and questions ready, restart the configured provider, verify readiness, then retry. Do not present deterministic test output as a real model result.
- Document stuck Processing: select **Refresh**; if it becomes Failed, inspect the safe API log message, correct the file or provider issue, and upload again.
- Browser retaining stale state: use **New chat**, reload once, or open a private window. Do not clear the database during the presentation.

## Pre-presentation checklist

- Mac connected to power
- Docker Desktop running
- Full stack started with `make dev`
- Live and readiness endpoints checked
- Real LLM provider verified privately
- Validation document ready in `docs/presentation/`
- Supported and unsupported questions ready
- Browser tabs prepared
- Notifications silenced
- Browser zoom checked
- Fallback screenshots captured only after the real-provider walkthrough passes
- No secrets visible in the terminal or browser

Stop the application safely with `Ctrl+C`, then run `make db-down` when local database services are no longer needed.
