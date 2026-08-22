from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import RetrievalRun, RetrievalRunResult
from app.services.ai.types import RetrievalCandidate, RetrievalFilters
from app.services.ingestion.persistence import vector_literal


def _metadata_page_number(metadata: dict[str, Any]) -> int | None:
    value = metadata.get("page_number") or metadata.get("page")
    return int(value) if isinstance(value, int | str) and str(value).isdigit() else None


class RetrievalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _filter_sql(self, filters: RetrievalFilters) -> tuple[str, dict[str, Any]]:
        clauses = ["s.status = 'active'", "s.last_successfully_ingested_at IS NOT NULL"]
        params: dict[str, Any] = {}
        if filters.latest_only:
            clauses.append(
                """
                d.version = (
                    SELECT max(latest.version)
                    FROM documents latest
                    WHERE latest.source_id = d.source_id
                )
                """
            )
        if filters.source_types:
            clauses.append("s.source_type = ANY(:source_types)")
            params["source_types"] = filters.source_types
        if filters.source_ids:
            clauses.append("s.id = ANY(:source_ids)")
            params["source_ids"] = [str(item) for item in filters.source_ids]
        if filters.document_ids:
            clauses.append("d.id = ANY(:document_ids)")
            params["document_ids"] = [str(item) for item in filters.document_ids]
        return " AND ".join(f"({clause})" for clause in clauses), params

    async def vector_candidates(
        self,
        *,
        query_vector: list[float],
        filters: RetrievalFilters,
        limit: int,
    ) -> list[RetrievalCandidate]:
        where_sql, params = self._filter_sql(filters)
        params.update({"query_vector": vector_literal(query_vector), "limit": limit})
        rows = (
            await self.session.execute(
                text(
                    f"""
                    SELECT
                      s.id AS source_id,
                      d.id AS document_id,
                      d.version AS document_version,
                      c.id AS chunk_id,
                      c.position AS chunk_position,
                      d.title,
                      s.display_name AS source_display_name,
                      CASE
                        WHEN s.source_type = 'url' THEN s.canonical_uri
                        ELSE NULL
                      END AS source_uri,
                      s.source_type,
                      c.heading_path,
                      c.content AS chunk_content,
                      c.chunk_checksum,
                      c.chunk_metadata,
                      row_number() OVER (
                        ORDER BY c.embedding <=> CAST(:query_vector AS vector), c.id
                      ) AS vector_rank,
                      c.embedding <=> CAST(:query_vector AS vector) AS vector_distance
                    FROM document_chunks c
                    JOIN documents d ON d.id = c.document_id
                    JOIN knowledge_sources s ON s.id = d.source_id
                    WHERE {where_sql}
                    ORDER BY c.embedding <=> CAST(:query_vector AS vector), c.id
                    LIMIT :limit
                    """
                ),
                params,
            )
        ).mappings()
        return [self._candidate_from_row(row) for row in rows]

    async def lexical_candidates(
        self,
        *,
        query_text: str,
        filters: RetrievalFilters,
        limit: int,
    ) -> list[RetrievalCandidate]:
        where_sql, params = self._filter_sql(filters)
        params.update({"query_text": query_text, "limit": limit})
        rows = (
            await self.session.execute(
                text(
                    f"""
                    WITH query AS (
                      SELECT websearch_to_tsquery('english', :query_text) AS tsq
                    )
                    SELECT
                      s.id AS source_id,
                      d.id AS document_id,
                      d.version AS document_version,
                      c.id AS chunk_id,
                      c.position AS chunk_position,
                      d.title,
                      s.display_name AS source_display_name,
                      CASE
                        WHEN s.source_type = 'url' THEN s.canonical_uri
                        ELSE NULL
                      END AS source_uri,
                      s.source_type,
                      c.heading_path,
                      c.content AS chunk_content,
                      c.chunk_checksum,
                      c.chunk_metadata,
                      row_number() OVER (
                        ORDER BY ts_rank_cd(c.search_vector, query.tsq) DESC, c.id
                      ) AS lexical_rank,
                      ts_rank_cd(c.search_vector, query.tsq) AS lexical_score
                    FROM document_chunks c
                    JOIN documents d ON d.id = c.document_id
                    JOIN knowledge_sources s ON s.id = d.source_id
                    CROSS JOIN query
                    WHERE {where_sql}
                      AND query.tsq @@ c.search_vector
                    ORDER BY lexical_score DESC, c.id
                    LIMIT :limit
                    """
                ),
                params,
            )
        ).mappings()
        return [self._candidate_from_row(row) for row in rows]

    async def persist_run(
        self,
        *,
        query_text: str | None,
        query_hash: str,
        query_length: int,
        applied_filters: dict[str, Any],
        configuration: dict[str, Any],
        algorithm_version: str,
        candidate_counts: dict[str, Any],
        reranking_mode: str,
        degraded_mode: dict[str, str] | None,
        latency_ms: dict[str, float],
        candidates: list[RetrievalCandidate],
    ) -> UUID:
        run = RetrievalRun(
            query_text=query_text,
            query_hash=query_hash,
            query_length=query_length,
            applied_filters=applied_filters,
            configuration=configuration,
            algorithm_version=algorithm_version,
            candidate_counts=candidate_counts,
            reranking_mode=reranking_mode,
            degraded_mode=degraded_mode,
            latency_ms=latency_ms,
        )
        self.session.add(run)
        await self.session.flush()
        for candidate in candidates:
            self.session.add(
                RetrievalRunResult(
                    retrieval_run_id=run.id,
                    chunk_id=candidate.chunk_id,
                    vector_rank=candidate.vector_rank,
                    vector_distance=candidate.vector_distance,
                    lexical_rank=candidate.lexical_rank,
                    lexical_score=candidate.lexical_score,
                    rrf_score=candidate.rrf_score,
                    reranker_score=candidate.reranker_score,
                    final_rank=candidate.final_rank,
                    selected=candidate.selected,
                    exclusion_reason=candidate.exclusion_reason,
                )
            )
        await self.session.flush()
        return run.id

    async def index_status(self) -> dict[str, bool]:
        rows = (
            await self.session.execute(
                text(
                    """
                    SELECT indexname FROM pg_indexes
                    WHERE tablename = 'document_chunks'
                      AND indexname IN (
                        'ix_document_chunks_embedding_hnsw',
                        'ix_document_chunks_search_vector'
                      )
                    """
                )
            )
        ).scalars()
        names = set(rows)
        return {
            "hnsw": "ix_document_chunks_embedding_hnsw" in names,
            "gin": "ix_document_chunks_search_vector" in names,
        }

    async def searchable_counts(self) -> dict[str, int]:
        row = (
            (
                await self.session.execute(
                    text(
                        """
                    WITH latest_docs AS (
                      SELECT DISTINCT ON (d.source_id) d.id, d.source_id
                      FROM documents d
                      JOIN knowledge_sources s ON s.id = d.source_id
                      WHERE s.status = 'active'
                        AND s.last_successfully_ingested_at IS NOT NULL
                      ORDER BY d.source_id, d.version DESC
                    )
                    SELECT
                      count(DISTINCT source_id) AS searchable_sources,
                      (
                        SELECT count(*)
                        FROM document_chunks c
                        JOIN latest_docs ld ON ld.id = c.document_id
                      )
                        AS searchable_chunks
                    FROM latest_docs
                    """
                    )
                )
            )
            .mappings()
            .one()
        )
        return {
            "searchable_sources": int(row["searchable_sources"]),
            "searchable_chunks": int(row["searchable_chunks"]),
        }

    def _candidate_from_row(self, row: Any) -> RetrievalCandidate:
        metadata = dict(row.get("chunk_metadata") or {})
        return RetrievalCandidate(
            source_id=row["source_id"],
            document_id=row["document_id"],
            document_version=row["document_version"],
            chunk_id=row["chunk_id"],
            chunk_position=row["chunk_position"],
            title=row["title"],
            source_display_name=row["source_display_name"],
            source_uri=row["source_uri"],
            source_type=row["source_type"],
            section_path=list(row["heading_path"] or []),
            page_number=_metadata_page_number(metadata),
            chunk_content=row["chunk_content"],
            chunk_checksum=row["chunk_checksum"],
            vector_rank=row.get("vector_rank"),
            vector_distance=row.get("vector_distance"),
            lexical_rank=row.get("lexical_rank"),
            lexical_score=row.get("lexical_score"),
        )
