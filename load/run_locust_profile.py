from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from load.environment import collect_environment
from load.profiles import PROFILES, profile
from load.reporting import summarize_locust_csv, write_summary


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _require_confirmation(profile_name: str, args: argparse.Namespace) -> bool:
    selected = profile(profile_name)
    if profile_name == "real-provider":
        if not args.confirm_real_provider or os.getenv("GROUNDSTACK_REAL_LOAD_ALLOWED") != "true":
            print(
                "real-provider requires --confirm-real-provider and "
                "GROUNDSTACK_REAL_LOAD_ALLOWED=true"
            )
            return False
        if int(args.max_requests or selected.max_requests) > 25:
            print("real-provider is capped at 25 requests by this runner.")
            return False
    if selected.requires_confirmation and not args.confirm:
        print(f"{profile_name} requires --confirm after reviewing local machine safety.")
        return False
    return True


def _command(args: argparse.Namespace, output_prefix: Path) -> tuple[list[str], dict[str, str]]:
    selected = profile(args.profile)
    users = args.users or selected.users
    spawn_rate = args.spawn_rate or selected.spawn_rate
    run_time = args.duration or selected.run_time
    max_requests = args.max_requests or selected.max_requests
    dataset = args.dataset or selected.dataset
    seed = args.seed or selected.seed
    return [
        sys.executable,
        "-m",
        "locust",
        "-f",
        "load/locustfile.py",
        "--host",
        args.host,
        "--csv",
        str(output_prefix),
        "--headless",
        "-u",
        str(users),
        "-r",
        str(spawn_rate),
        "--run-time",
        run_time,
    ], {
        "GROUNDSTACK_LOAD_MAX_REQUESTS": str(max_requests),
        "GROUNDSTACK_LOAD_QUESTIONS": dataset,
        "GROUNDSTACK_LOAD_SEED": str(seed),
        "LLM_PROVIDER": selected.provider_mode
        if selected.provider_mode != "hosted"
        else "openai_compatible",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a GroundStack deterministic load profile.")
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument(
        "--host", default=os.getenv("GROUNDSTACK_LOAD_HOST", "http://localhost:8000")
    )
    parser.add_argument("--users", type=int)
    parser.add_argument("--spawn-rate", type=float)
    parser.add_argument("--duration")
    parser.add_argument("--dataset")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--max-requests", type=int)
    parser.add_argument("--output-dir", default="load/reports")
    parser.add_argument(
        "--corpus-version", default=os.getenv("GROUNDSTACK_CORPUS_VERSION", "local")
    )
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--confirm-real-provider", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not _require_confirmation(args.profile, args):
        return 2

    selected = profile(args.profile)
    stamp = _timestamp()
    report_dir = Path(args.output_dir) / f"{args.profile}-{stamp}"
    report_dir.mkdir(parents=True, exist_ok=False)
    output_prefix = report_dir / "locust"
    command, env_overrides = _command(args, output_prefix)
    environment = collect_environment()
    manifest: dict[str, Any] = {
        "profile": selected.to_dict(),
        "started_at": datetime.now(UTC).isoformat(),
        "host": args.host,
        "corpus_version": args.corpus_version,
        "command": command,
        "env_overrides": {key: value for key, value in env_overrides.items() if "KEY" not in key},
        "environment": environment,
        "success_criteria": [
            "No malformed successful responses",
            "No 5xx responses",
            "Terminal SSE event for chat streams",
            "Citation schema valid when citations are present",
        ],
        "limitations": [
            "Synthetic workload, not production usage",
            "Local machine resource constraints apply",
            "Provider mode is recorded separately from application capacity",
        ],
    }
    (report_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    if args.dry_run:
        write_summary(
            report_dir / "summary.json",
            {
                "dry_run": True,
                "profile": selected.to_dict(),
                "results": {"total_requests": 0, "failures": 0, "success_rate": 0.0},
                "evidence_paths": [str(report_dir / "manifest.json")],
            },
        )
        print(f"dry_run_report={report_dir}")
        return 0

    env = os.environ.copy()
    env.update(env_overrides)
    exit_code = subprocess.call(command, env=env)
    summary = summarize_locust_csv(report_dir / "locust_stats.csv")
    write_summary(
        report_dir / "summary.json",
        {
            "dry_run": False,
            "exit_code": exit_code,
            "profile": selected.to_dict(),
            "results": {
                "total_requests": summary.total_requests,
                "failures": summary.failures,
                "success_rate": summary.success_rate,
                "median_ms": summary.median_ms,
                "p95_ms": summary.p95_ms,
                "p99_ms": summary.p99_ms,
            },
            "evidence_paths": [
                str(report_dir / "manifest.json"),
                str(report_dir / "summary.json"),
                str(report_dir / "locust_stats.csv"),
            ],
        },
    )
    print(f"report={report_dir}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
