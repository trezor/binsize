from __future__ import annotations

import shutil
import subprocess
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, Sequence

import click

from binsize import settings

from .. import get_sections_sizes

ELF_FILE = settings.get("elf_file")
BUILD_CMD = settings.get("build_cmd")


def run_cmd(cmd: list[str]) -> None:
    print(f"Running {cmd}")
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL)


def get_commit_hashes(amount_in_past: int = 10_000) -> list[str]:
    commit_hashes = subprocess.check_output(
        ["git", "log", "--pretty=format:%H", "-n", str(amount_in_past)]
    )
    return commit_hashes.decode().splitlines()


def get_commit_timestamp(commit_hash: str) -> int:
    commit_timestamp = subprocess.check_output(
        ["git", "show", "-s", "--format=%ct", commit_hash]
    )
    return int(commit_timestamp.decode())


def get_commit_date(commit_hash: str) -> str:
    commit_timestamp = get_commit_timestamp(commit_hash)
    return datetime.fromtimestamp(commit_timestamp).strftime("%Y-%m-%d")


def get_current_branch_name() -> str:
    return (
        subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        .decode()
        .strip()
    )


def get_current_commit_hash() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()


def are_there_local_changes() -> bool:
    return subprocess.call(["git", "diff", "--quiet", "--exit-code"]) != 0


def get_fw_path(commit_hash: str) -> Path:
    return Path(f"{ELF_FILE}_{commit_hash}")


@contextmanager
def change_to_commit_and_back(commit_hash: str) -> Generator[None, None, None]:
    current_branch = get_current_branch_name()
    local_changes = are_there_local_changes()
    if local_changes:
        run_cmd(["git", "stash"])
    run_cmd(["git", "checkout", commit_hash])
    yield
    run_cmd(["git", "reset", "--hard", "HEAD"])
    run_cmd(["git", "checkout", current_branch])
    if local_changes:
        run_cmd(["git", "stash", "pop"])


def build_and_rename_fw(commit_hash: str) -> None:
    new_path = get_fw_path(commit_hash)
    if new_path.exists():
        print(f"Binary already exists for commit {commit_hash}")
        return

    with change_to_commit_and_back(commit_hash):
        print(f"Building binary for commit {commit_hash}...")
        run_cmd(BUILD_CMD.split())
        shutil.copyfile(ELF_FILE, new_path)


def create_binaries(commit_hashes: list[str]) -> None:
    for commit_hash in commit_hashes:
        print(commit_hash, get_commit_date(commit_hash))
        build_and_rename_fw(commit_hash)


def analyze_sizes(
    commit_hashes: list[str], sections: Sequence[str] | None = None
) -> None:
    sizes: dict[str, dict[str, int]] = {}
    for commit_hash in commit_hashes:
        print(commit_hash[:8], get_commit_date(commit_hash))
        fw_path = get_fw_path(commit_hash)
        if not fw_path.exists():
            print(f"Binary not found for commit {commit_hash}")
            continue
        size = get_sections_sizes(fw_path, sections)
        print("size", size)
        sizes[commit_hash] = size
    for commit_hash, size in sizes.items():
        print(commit_hash[:8], get_commit_date(commit_hash), size)


def generate_hashes_from_past(in_past: int, step: int) -> list[str]:
    all_commit_hashes = get_commit_hashes(in_past)
    commit_hashes = [
        all_commit_hashes[i] for i in range(0, len(all_commit_hashes), step)
    ]
    return list(reversed(commit_hashes))


@click.command()
@click.argument("commits", type=int, default=500)
@click.argument("step", type=int, default=15)
@click.option(
    "-s", "--sections", multiple=True, help="Sections which to analyze. All if not set."
)
def history(commits: int, step: int, sections: list[str]) -> None:
    """Show the size of the binary over time."""
    print(f"Going {commits} commits into past with step {step}")

    commit_hashes = generate_hashes_from_past(commits, step)
    create_binaries(commit_hashes)
    analyze_sizes(commit_hashes, sections)


if __name__ == "__main__":
    history()
