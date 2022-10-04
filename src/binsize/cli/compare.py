"""
>>> compare.py /path/to/firmware.elf_version25 /path/to/firmware.elf_version1 -d -o diff.txt
- compares size differences in flash sections of these two binaries
- with all details, saved to file
"""

from __future__ import annotations

import click

from .. import show_binaries_diff


@click.command()
@click.argument("bin1")
@click.argument("bin2")
@click.option("-o", "--output-file", help="Dump results to file instead of stdout")
@click.option(
    "-s", "--sections", multiple=True, help="Sections which to analyze. All if not set."
)
@click.option(
    "-d", "--details", is_flag=True, help="Include all details (line definitions)"
)
def compare(
    bin1: str,
    bin2: str,
    output_file: str,
    sections: list[str],
    details: bool,
) -> None:
    """Compare two binaries."""
    file_to_save = output_file or None
    show_binaries_diff(
        bin1, bin2, all_details=details, sections=sections, file_to_save=file_to_save
    )


if "__main__" == __name__:
    compare()
