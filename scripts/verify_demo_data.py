from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import async_session_factory
from app.models.knowledge import Document, KnowledgeSource

CORPUS_ID = "northstar-systems-support-demo"
EXPECTED_DOCUMENTS = 10


async def _northstar_counts() -> tuple[int, int, int]:
    async with async_session_factory() as session:
        result = await session.execute(
            select(KnowledgeSource).options(
                selectinload(KnowledgeSource.documents).selectinload(Document.chunks)
            )
        )
        sources = [
            source
            for source in result.scalars()
            if source.source_metadata.get("corpus_id") == CORPUS_ID and source.status == "active"
        ]
        documents = sum(len(source.documents) for source in sources)
        chunks = sum(len(document.chunks) for source in sources for document in source.documents)
        return len(sources), documents, chunks


def main() -> int:
    sources, documents, chunks = asyncio.run(_northstar_counts())
    print(f"northstar_demo_sources={sources}")
    print(f"northstar_demo_documents={documents}")
    print(f"northstar_demo_chunks={chunks}")
    if (
        sources != EXPECTED_DOCUMENTS
        or documents != EXPECTED_DOCUMENTS
        or chunks < EXPECTED_DOCUMENTS
    ):
        print(
            "Northstar demo verification failed: expected 10 active sources, "
            "10 document versions, and at least one chunk per document."
        )
        return 1
    print("Northstar demo data verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
