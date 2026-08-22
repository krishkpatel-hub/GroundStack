import argparse
import asyncio
from pathlib import Path

from app.services.ingestion.orchestrator import IngestionOrchestrator
from app.services.ingestion.sources import file_input_from_path


async def ingest_path(path: Path) -> None:
    orchestrator = IngestionOrchestrator()
    paths = sorted(path.glob("*")) if path.is_dir() else [path]
    for item in paths:
        if not item.is_file():
            continue
        job_id = await orchestrator.create_job()
        report = await orchestrator.ingest(job_id, file_input_from_path(item))
        print(
            f"{item}: {report.status} "
            f"document={report.document_id} version={report.version} chunks={report.chunk_count}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest GroundStack knowledge files.")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    asyncio.run(ingest_path(args.path))


if __name__ == "__main__":
    main()
