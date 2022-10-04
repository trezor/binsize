"""
>>> size.py build version25
- builds the binary and copies it as `<elf_file>_version25`
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import click

from .. import settings


@click.command()
@click.argument("name", required=False)
def build(
    name: str,
) -> None:
    """Build a binary and optionally give it a new name."""
    build_binary(name)


def build_binary(extra_suffix: str | None = None) -> None:
    build_cmd = settings.get("build_cmd")
    print(f"building the binary... `{build_cmd}`")

    build_result = subprocess.run(
        build_cmd, stdout=subprocess.PIPE, text=True, shell=True
    )
    if build_result.returncode != 0:
        print("build failed - see output above")
        exit(1)

    # Optionally copying the binary to a special name, to be used later
    if extra_suffix is not None:
        elf_file = settings.get("elf_file")

        new_path = Path(f"{elf_file}_{extra_suffix}")
        shutil.copyfile(elf_file, new_path)
        print(f"Binary copied as `{new_path}`")


if "__main__" == __name__:
    build()
