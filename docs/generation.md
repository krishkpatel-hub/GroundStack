# GroundStack Grounded Generation

GroundStack generates answers only after retrieval has selected source chunks. The
LLM receives a versioned system prompt, recent completed conversation turns, and
source blocks with explicit citation IDs such as `S1`.

## Providers

Default local provider:

```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2:3b
LLM_BASE_URL=http://localhost:11434
ollama pull llama3.2:3b
```

OpenAI-compatible provider:

```bash
LLM_PROVIDER=openai_compatible
LLM_MODEL=your-model
LLM_BASE_URL=http://localhost:8001
LLM_API_KEY=optional-secret
```

The OpenAI-compatible provider expects `/v1/models` and `/v1/chat/completions`.

## API

- `POST /api/v1/chat` returns the final persisted answer.
- `POST /api/v1/chat/stream` streams Server-Sent Events.
- `GET /api/v1/conversations` lists saved conversations.
- `GET /api/v1/conversations/{id}/messages` returns persisted messages and
  citation IDs.

The stream can emit:

- `conversation`
- `retrieval_started`
- `retrieval_completed`
- `generation_started`
- `token`
- `usage`
- `repair_started`
- `canonical_answer`
- `completed`
- `error`

## Persistence

Generation writes:

- user and assistant messages
- generation runs with provider/model/prompt metadata
- prompt checksum and optional rendered prompt
- context citation IDs and token-counting mode
- token usage, latency, finish reason, repair attempts, and error metadata
- message-to-chunk citation links

## Grounding Rules

If retrieval finds no evidence, GroundStack returns an insufficient-evidence answer
without calling the LLM.

If the LLM produces unsupported citations, malformed citations, or a substantive
answer with no citations, GroundStack attempts one repair pass. If repair fails, the
assistant message is persisted as failed with `citation_validation_failed`.

The citation validator ignores citations inside fenced code blocks and only accepts
IDs assigned by the retrieval run.

## UI

The home page is a streaming chat surface with saved conversation history, source
filters, stop/retry controls, Markdown rendering through `react-markdown`, copyable
code blocks, and citation inspection. The sidebar status includes LLM provider/model
availability from `/api/v1/system/status`.
