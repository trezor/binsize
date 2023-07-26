"""
Main entry-point of the CLI for the `binsize` command.
"""

from __future__ import annotations

import click
import sys

from .. import set_root_dir
from . import build, commit, compare, get, history, tree


@click.group(invoke_without_command=True)
@click.option("-r", "--root-dir", help="Root directory of the project")
@click.option("-v", "--version", is_flag=True, help="Show current version and exit")
def cli(root_dir: str | None, version: bool) -> None:
    """
    CLI for binary size analysis based on `.elf` file.

    Requires `bloaty` and `nm` to run.

    See subcommands for details.
    """
    if version:
        from .. import __version__

        click.echo(__version__)
        sys.exit(0)
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
