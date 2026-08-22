# GroundStack Retrieval

GroundStack retrieves source evidence from the ingested knowledge base. Retrieval
returns stored chunks, ranks, citations, timing, and degraded-mode state. The chat
generation path uses this same retrieval result as its only answer context.

## Flow

```text
User query
-> Unicode and whitespace normalization
-> query embedding
-> pgvector cosine search
-> PostgreSQL full-text search
-> Reciprocal Rank Fusion
-> optional cross-encoder reranking
-> deterministic diversity selection
-> citations
-> retrieval diagnostics persistence
```

## Vector Search

The semantic channel uses the production `EmbeddingProvider` and `encode_query`
behavior exposed by Sentence Transformers when the model supports prompts. Query
vectors must match `EMBEDDING_DIMENSION`, currently `384`. The database performs
cosine-distance ordering with pgvector; GroundStack does not load all stored
embeddings into application memory.

By default retrieval searches only active sources with a successful ingestion
timestamp and the latest document version for each source.

## PostgreSQL Text Search

The lexical channel uses `websearch_to_tsquery('english', query)` against the
indexed generated `search_vector` column and ranks with `ts_rank_cd`. This is
PostgreSQL full-text search, not BM25.

## Reciprocal Rank Fusion

RRF merges vector and lexical ranks without averaging incomparable raw scores:

```text
score =
VECTOR_RRF_WEIGHT / (RRF_K + vector_rank)
+ LEXICAL_RRF_WEIGHT / (RRF_K + lexical_rank)
```

Missing ranks contribute zero. Ties are broken deterministically by rank, title,
chunk position, and chunk ID.

## Reranking

When enabled, GroundStack reranks only the fused candidate set with
`cross-encoder/ms-marco-MiniLM-L6-v2`. The model loads lazily and runs off the
async event loop. Raw cross-encoder logits are used for ordering only; they are not
calibrated confidence probabilities. If reranking fails, the response declares
degraded mode and returns the fused RRF order.

## Diversity

Final selection removes exact duplicate chunk checksums, limits selected chunks per
source, and keeps deterministic exclusion reasons such as `source_limit`,
`duplicate_chunk_checksum`, or `below_final_cut`.

## Citations

Each selected chunk becomes a citation with a stable ID (`S1`, `S2`, ...), source
ID, document ID and version, chunk ID, title, source display name, source type,
canonical URL when available, section path, page number when available, excerpt, and
final rank. Citation order matches retrieval order. Excerpts are plain text and are
never generated from unstored content.

## Filters

Search accepts source type, source ID, and document ID filters. The same filters are
applied to vector and lexical channels.

## Query Privacy

Retrieval logs include query hash, query length, candidate counts, latency, and
degraded-mode reason. They do not log full query text, chunks, embeddings, credentials,
or sensitive URL parameters. Raw query persistence is controlled by
`PERSIST_RETRIEVAL_QUERIES` and defaults to `false`.

## Evaluation

`make eval-retrieval` runs the sample retrieval dataset and measures vector-only,
lexical-only, hybrid RRF, and hybrid reranked modes. It reports Recall@5,
Recall@10, MRR@10, nDCG@10, unsupported-query behavior, dataset checksum, model
names, configuration, and timestamp. Results are baselines, not production-quality
claims.

`make benchmark-retrieval` separates model cold start from warm-query latency and
reports median and p95 stage timings.

## Current Limitations

- The development corpus is tiny, so PostgreSQL may choose sequential scans even
  though HNSW and GIN indexes exist.
- There is no calibrated no-answer threshold yet, so semantic retrieval can return
  neighboring evidence for unsupported queries.
- Auth, fine-tuning, calibrated answer-quality evaluation, and deployment are not
  implemented in this milestone.
