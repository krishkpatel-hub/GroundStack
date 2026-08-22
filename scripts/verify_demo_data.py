from __future__ import annotations

import asyncio

from sqlalchemy import func, select

from app.db.session import async_session_factory
from app.models.knowledge import Document, DocumentChunk, KnowledgeSource


async def _counts() -> tuple[int, int, int]:
    async with async_session_factory() as session:
        sources = await session.scalar(select(func.count()).select_from(KnowledgeSource))
        documents = await session.scalar(select(func.count()).select_from(Document))
        chunks = await session.scalar(select(func.count()).select_from(DocumentChunk))
        return int(sources or 0), int(documents or 0), int(chunks or 0)


def main() -> int:
    sources, documents, chunks = asyncio.run(_counts())
    print(f"demo_sources={sources}")
    print(f"demo_documents={documents}")
    print(f"demo_chunks={chunks}")
    if sources < 2 or documents < 2 or chunks < 2:
        print("Demo data verification failed: expected at least 2 sources/documents/chunks.")
        return 1
    print("Demo data verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
