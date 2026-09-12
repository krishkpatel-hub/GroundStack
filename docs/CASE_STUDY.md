# GroundStack Case Study

## Problem

Organizations often keep procedures and technical knowledge in disconnected documents.
Searching manually is slow, while a general chatbot may answer without evidence or require
employees to paste sensitive material into an unrelated public service.

## Solution

GroundStack provides an administrator-managed knowledge base. It validates and processes
approved documents, stores embeddings in PostgreSQL with pgvector, retrieves a small set of
relevant sections, and asks one OpenAI-compatible model to answer only from that evidence.
Every accepted source reference is validated before the answer is saved.

## Engineering Decisions

- A single Next.js app and FastAPI API keep the project understandable and deployable.
- PostgreSQL stores product data and pgvector embeddings in one transactional system.
- A fixed vector-distance threshold makes the evidence gate explicit.
- Missing evidence returns a stable refusal before generation.
- Provider errors do not save a misleading completed answer.
- Development authentication is deliberately local-only; hosted use requires configured OIDC.

## Evidence

The repository includes unit, API, browser, migration, backup/restore, authorization,
ingestion, retrieval, and citation tests. Browser tests use mocked API responses and provider
tests use deterministic output; neither is presented as external-provider validation.

## Current Boundary

GroundStack is a portfolio project, not a deployed municipal or commercial system. Privacy
depends on the chosen hosting, identity, logging, retention, and model-provider configuration.
