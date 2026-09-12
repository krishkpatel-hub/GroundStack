from __future__ import annotations

import argparse
import asyncio
from dataclasses import replace
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import async_session_factory
from app.models.knowledge import KnowledgeSource
from app.services.ingestion.orchestrator import IngestionOrchestrator
from app.services.ingestion.sources import file_input_from_path

CORPUS_ID = "northstar-systems-support-demo"
CORPUS_VERSION = "northstar-support-v1"
CORPUS_ROOT = Path("docs/demo-corpus/northstar")


def corpus_paths(root: Path) -> list[Path]:
    return sorted(path for path in root.glob("*.md") if path.is_file())


def northstar_input(path: Path):
    payload = file_input_from_path(path)
    return replace(
        payload,
        source_metadata={
            **payload.source_metadata,
            "corpus_id": CORPUS_ID,
            "corpus_version": CORPUS_VERSION,
            "organization": "Northstar Systems",
            "fictional_demo": True,
        },
    )


async def reset_northstar_corpus() -> int:
    async with async_session_factory() as session:
        result = await session.execute(
            select(KnowledgeSource).options(selectinload(KnowledgeSource.documents))
        )
        sources = [
            source
            for source in result.scalars()
            if source.source_metadata.get("corpus_id") == CORPUS_ID
        ]
        for source in sources:
            await session.delete(source)
        await session.commit()
        return len(sources)


async def ingest_northstar_corpus(root: Path) -> list[str]:
    paths = corpus_paths(root)
    if not paths:
        raise SystemExit(f"No Northstar demo documents found in {root}")
    orchestrator = IngestionOrchestrator()
    reports: list[str] = []
    for path in paths:
        job_id = await orchestrator.create_job()
        report = await orchestrator.ingest(job_id, northstar_input(path))
        reports.append(f"{path.name}: {report.status} ({report.chunk_count} chunks)")
    return reports


async def run(*, reset: bool) -> None:
    root = Path(__file__).resolve().parents[1]
    corpus_root = root / CORPUS_ROOT
    if reset:
        deleted = await reset_northstar_corpus()
        print(f"Reset Northstar demo corpus: deleted {deleted} source(s).")
    reports = await ingest_northstar_corpus(corpus_root)
    print("Seeded Northstar Systems fictional demo corpus:")
    for line in reports:
        print(f"- {line}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed the fictional Northstar Systems support corpus."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete previously seeded Northstar demo sources before reingesting.",
    )
    args = parser.parse_args()
    asyncio.run(run(reset=args.reset))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
