"""
Checking the size differences introduced by a specified commit.
"""

from __future__ import annotations

import click

from .. import get_sections_sizes
from .history import build_and_rename_fw, get_commit_hashes, get_fw_path


def get_previous_commit_hash(commit_hash: str) -> tuple[str, str]:
    commit_hashes = get_commit_hashes()
    for index, commit in enumerate(commit_hashes):
        if commit.startswith(commit_hash):
            # returning full commit hash as well to unify its length
            return commit, commit_hashes[index + 1]

    raise ValueError(f"Commit {commit_hash} not found")


@click.command()
@click.argument("commit_hash")
@click.option(
    "-s", "--sections", multiple=True, help="Sections which to analyze. All if not set."
)
def commit(commit_hash: str, sections: list[str]) -> None:
    """Show how much commit affected binary size."""
    full_hash, previous_hash = get_previous_commit_hash(commit_hash)

    build_and_rename_fw(full_hash)
    build_and_rename_fw(previous_hash)

    current_size = get_sections_sizes(get_fw_path(full_hash), sections)
    previous_size = get_sections_sizes(get_fw_path(previous_hash), sections)

    diff = {
        section: current_size[section] - previous_size[section]
        for section in current_size
    }
    print("diff", diff)


if __name__ == "__main__":
    commit()
