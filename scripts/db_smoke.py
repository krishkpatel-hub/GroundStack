from __future__ import annotations

import asyncio

from sqlalchemy import text

from app.db.session import async_session_factory


async def _smoke() -> tuple[str, str]:
    async with async_session_factory() as session:
        version = await session.scalar(text("select version()"))
        vector = await session.scalar(
            text("select extversion from pg_extension where extname = 'vector'")
        )
    return str(version or "unknown"), str(vector or "missing")


def main() -> int:
    version, vector = asyncio.run(_smoke())
    print(f"postgres={version.split(',')[0]}")
    print(f"pgvector={vector}")
    if vector == "missing":
        print("Database smoke failed: pgvector extension is not enabled.")
        return 1
    print("Database smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
