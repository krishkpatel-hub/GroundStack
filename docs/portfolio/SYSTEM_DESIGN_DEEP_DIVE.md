# System Design Deep Dive

## Why RAG And Fine-Tuning Are Separate

RAG answers source-specific questions using current documents and citations. Fine-tuning can shape
style or repeated behavior, but it does not replace retrieval when the answer must point to current
project documentation. GroundStack therefore treats reviewed training data as an offline improvement
workflow, not as the runtime source of truth.

## Retrieval And Reranking

GroundStack stores normalized chunks with embeddings and PostgreSQL text-search vectors. Queries run
vector search, full-text search, RRF fusion, optional cross-encoder reranking, and diversity
selection before assigning structured citation IDs.

## Hallucination Controls

Generated answers must cite retrieved source IDs. Citation validation rejects fabricated or malformed
IDs and attempts one repair. If no evidence is available, GroundStack abstains before calling the
LLM.

## Reliability And Cost

Demo limits, provider concurrency, Discord per-user/channel/guild limits, and deterministic load
profiles keep capacity testing separate from production claims. Hosted-provider testing is opt-in and
cost-aware.

## Scaling To A Real Large Community

A real 50,000-member community would require tenant/workspace isolation, durable queues, live Discord
sandbox evidence, production observability, incident response, cost budgets, moderation workflows,
and a measured SLO baseline. GroundStack `1.0.0-rc.1` documents these as future production work.
