#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPROVED_PLACEHOLDERS = {
    ".env.example",
    "deploy/.env.demo.example",
}
SCANNER_PATH = Path(__file__).resolve().relative_to(ROOT).as_posix()


@dataclass(frozen=True)
class SecretPattern:
    name: str
    pattern: re.Pattern[str]


PATTERNS = [
    SecretPattern("private-key", re.compile(r"BEGIN (RSA|OPENSSH|EC) PRIVATE KEY")),
    SecretPattern("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}")),
    SecretPattern("oidc-client-secret", re.compile(r"OIDC_CLIENT_SECRET=.+")),
]


def _tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=False,
    )
    files = []
    for raw in result.stdout.split(b"\0"):
        if raw:
            files.append(ROOT / raw.decode("utf-8"))
    return files


def _display(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _should_skip(path: Path) -> bool:
    display = _display(path)
    return display in APPROVED_PLACEHOLDERS or display == SCANNER_PATH


def _scan_file(path: Path) -> list[tuple[int, str]]:
    if _should_skip(path) or not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    findings = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for secret in PATTERNS:
            if secret.pattern.search(line):
                findings.append((line_number, secret.name))
    return findings


def scan(paths: Iterable[Path]) -> list[str]:
    violations = []
    for path in paths:
        for line_number, pattern_name in _scan_file(path):
            violations.append(f"{_display(path)}:{line_number}: matched {pattern_name}")
    return violations


def self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="groundstack-secret-scan-") as temp_dir:
        fixture = Path(temp_dir) / "fixture.txt"
        fixture.write_text("token = " + "AKIA" + ("0" * 16) + "\n", encoding="utf-8")
        if not scan([fixture]):
            print("self-test failed: seeded fake secret was not detected", file=sys.stderr)
            return 1
        placeholder_violations = scan(ROOT / path for path in APPROVED_PLACEHOLDERS)
        if placeholder_violations:
            print("self-test failed: approved placeholders raised findings", file=sys.stderr)
            return 1
        implementation_violations = scan([ROOT / SCANNER_PATH])
        if implementation_violations:
            print("self-test failed: scanner implementation raised findings", file=sys.stderr)
            return 1
    print("secret scan self-test passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan tracked files for committed secrets.")
    parser.add_argument("--self-test", action="store_true", help="Run scanner self-tests.")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    violations = scan(_tracked_files())
    if violations:
        print("Potential secrets detected. Values are intentionally not printed.", file=sys.stderr)
        for violation in violations:
            print(violation, file=sys.stderr)
        return 1
    print("secret scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
