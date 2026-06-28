"""Create a safe git checkpoint commit for this repository."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


DEFAULT_TEST_COMMAND = r".\.venv\Scripts\python.exe -m pytest"


def run(command: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        raise SystemExit(result.returncode)
    return result


def repo_root() -> Path:
    result = run(["git", "rev-parse", "--show-toplevel"], Path.cwd())
    return Path(result.stdout.strip())


def git_status(cwd: Path) -> str:
    return run(["git", "status", "--short"], cwd).stdout.strip()


def run_validation(cwd: Path, command: str) -> None:
    result = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        raise SystemExit(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a git checkpoint commit.")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional paths to stage. Defaults to all non-ignored changes.",
    )
    parser.add_argument("--message", "-m", required=True, help="Commit message.")
    parser.add_argument(
        "--test-command",
        default=DEFAULT_TEST_COMMAND,
        help="Validation command to run before committing.",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip validation only after an explicit decision.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show actions only.")
    args = parser.parse_args()

    cwd = repo_root()
    before_status = git_status(cwd)
    if not before_status:
        print("No changes to checkpoint.")
        return 0

    print("Current changes:")
    print(before_status)

    if args.dry_run:
        print("\nDry run only. No files staged or committed.")
        return 0

    if not args.skip_tests:
        print(f"\nRunning validation: {args.test_command}")
        run_validation(cwd, args.test_command)

    add_command = ["git", "add", "--all", "--"]
    add_command.extend(args.paths or ["."])
    run(add_command, cwd)

    staged = run(["git", "diff", "--cached", "--name-only"], cwd).stdout.strip()
    if not staged:
        print("No staged changes after applying scope.")
        return 0

    print("\nStaged files:")
    print(staged)

    run(["git", "commit", "-m", args.message], cwd)
    commit_hash = run(["git", "rev-parse", "--short", "HEAD"], cwd).stdout.strip()
    print(f"\nCreated checkpoint commit {commit_hash}: {args.message}")

    remaining = git_status(cwd)
    if remaining:
        print("\nRemaining uncommitted changes:")
        print(remaining)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
