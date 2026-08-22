# Architecture Talk Track

GroundStack is split into a frontend, API, data layer, and model provider. Next.js owns the product
experience and streams chat events from FastAPI. The backend normalizes documents, chunks them,
stores embeddings in pgvector, runs hybrid vector and lexical retrieval, reranks candidates, and
builds a bounded prompt with citation IDs.

Generation is provider-abstracted. Local development uses Ollama; the public demo is prepared for an
OpenAI-compatible hosted LLaMA endpoint. The API records provider/model metadata, validates citations,
captures feedback, and exposes evaluation/admin workflows only behind auth. Public demo mode adds
anonymous rate limits, daily capacity, a kill switch, and sanitized availability states.
