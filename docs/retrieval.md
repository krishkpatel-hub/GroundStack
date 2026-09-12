# Semantic Retrieval

GroundStack uses one retrieval channel: cosine-distance search over embeddings stored in
pgvector.

1. Normalize and validate the question.
2. Create a query embedding with the same model and dimension used during ingestion.
3. Search only active sources with a completed ingestion.
4. Fetch at most `RETRIEVAL_CANDIDATE_LIMIT` candidates.
5. Reject candidates beyond `RETRIEVAL_MAX_VECTOR_DISTANCE`.
6. Return at most `RETRIEVAL_MAX_TOP_K` sections.
7. Convert selected sections into numbered source records.

The default distance threshold is `0.45`. Lower cosine distance indicates a closer match.
The threshold is an explicit product setting, not a calibrated probability, and should be
evaluated against the organization's approved documents before serious use.

Queries are hashed for diagnostics. Full query persistence is disabled by default.
