# GroundStack Roadmap

## Completed: Ingestion, Retrieval, And Grounded Generation

GroundStack can ingest Markdown, text, HTML, text-based PDF, and one allowlisted
public URL at a time. It stores source lineage, immutable document versions, chunks,
text-search vectors, embeddings, and ingestion jobs.

GroundStack can search that knowledge base with pgvector retrieval, PostgreSQL
full-text retrieval, Reciprocal Rank Fusion, optional cross-encoder reranking, source
diversity, persisted diagnostics, and structured citations.

GroundStack can also stream grounded answers from a configured Ollama or
OpenAI-compatible LLM provider, validate inline citations, persist conversations and
generation runs, and return deterministic insufficient-evidence responses.

## 1. Feedback And Evaluation

Capture user ratings, issue labels, corrected answers, source quality signals, and
answer faithfulness checks. Feed approved examples into regression suites and future
training datasets.

## 2. Durable Orchestration

Move process-local background work behind durable workers for ingestion,
generation, retries, and long-running evaluations.

## 3. Fine-Tuning

Build a reproducible LoRA/QLoRA supervised fine-tuning pipeline with versioned datasets, model cards, training configs, and evaluation gates.

## 4. Observability and Deployment

Add structured request tracing, metrics, dashboards, load testing, deployment manifests, backup plans, and runtime alerts.
