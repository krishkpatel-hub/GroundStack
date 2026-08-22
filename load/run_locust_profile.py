from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


PROFILES = {
    "fake-smoke": ["--headless", "-u", "2", "-r", "1", "--run-time", "20s"],
    "fake-sustained": ["--headless", "-u", "8", "-r", "2", "--run-time", "5m"],
    "real-300": ["--headless", "-u", "3", "-r", "1", "--run-time", "24h"],
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a GroundStack Locust profile.")
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--host", default=os.getenv("GROUNDSTACK_LOAD_HOST", "http://localhost:8000"))
    parser.add_argument("--require-real", action="store_true")
    args = parser.parse_args()
    if args.profile == "real-300" and (
        not args.require_real or os.getenv("GROUNDSTACK_REAL_LOAD_ALLOWED") != "true"
    ):
        print("real-300 requires --require-real and GROUNDSTACK_REAL_LOAD_ALLOWED=true")
        return 2
    report_dir = Path("load/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    stats_prefix = report_dir / f"{args.profile}-{stamp}"
    command = [
        sys.executable,
        "-m",
        "locust",
        "-f",
        "load/locustfile.py",
        "--host",
        args.host,
        "--csv",
        str(stats_prefix),
        *PROFILES[args.profile],
    ]
    metadata = {
        "profile": args.profile,
        "host": args.host,
        "started_at": datetime.now(UTC).isoformat(),
        "command": command,
    }
    (report_dir / f"{args.profile}-{stamp}.manifest.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8"
    )
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
