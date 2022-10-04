"""
Main entry-point of the CLI for the `binsize` command.
"""

from __future__ import annotations

import click

from .. import set_root_dir
from . import build, commit, compare, get, history, tree


@click.group()
@click.option("-r", "--root-dir", help="Root directory of the project")
def cli(root_dir: str | None) -> None:
    """
    CLI for binary size analysis based on `.elf` file.

    Requires `bloaty` and `nm` to run.

    See subcommands for details.
    """
    if root_dir:
        set_root_dir(root_dir)


cli.add_command(build.build)
cli.add_command(commit.commit)
cli.add_command(compare.compare)
cli.add_command(get.get)
cli.add_command(history.history)
cli.add_command(tree.tree)


if __name__ == "__main__":
    cli()
