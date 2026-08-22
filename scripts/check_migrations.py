from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def main() -> int:
    config = Config("apps/api/alembic.ini")
    config.set_main_option("script_location", str(Path("apps/api/migrations")))
    script = ScriptDirectory.from_config(config)
    heads = script.get_heads()
    if len(heads) != 1:
        print(f"Migration check failed: expected one head, found {heads}")
        return 1
    print(f"Migration check passed: head={heads[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
