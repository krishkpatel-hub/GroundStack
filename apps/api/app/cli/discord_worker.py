from __future__ import annotations

import asyncio
import sys

from app.core.settings import get_settings
from app.services.discord.worker import process_discord_jobs_once


async def _main() -> int:
    if "--healthcheck" in sys.argv:
        settings = get_settings()
        print(
            "discord_worker_health=ok "
            f"integration_enabled={str(settings.discord_integration_enabled).lower()} "
            f"batch_size={settings.discord_worker_batch_size}"
        )
        return 0
    processed = await process_discord_jobs_once()
    print(f"processed_discord_jobs={processed}")
    return 0


def main() -> int:
    return asyncio.run(_main())


if __name__ == "__main__":
    raise SystemExit(main())
