"""
Getting information the size of symbols stored in the binary.

Example usage:
>>> get.py ELF_FILE --language Rust
- shows just Rust symbols
>>> get.py ELF_FILE --add-definitions
- including line numbers of definitions
>>> get.py ELF_FILE --module-name src/apps/bitcoin/sign_tx/bitcoin.py
- shows all functions from src/apps/bitcoin/sign_tx/bitcoin.py file
>>> get.py ELF_FILE --module-name '*__init__.py'
- shows all functions from all __init__.py files
>>> get.py ELF_FILE --func-name step2_approve_outputs --add-definitions
- shows all the rows with this function, with a definition
>>> get.py ELF_FILE --func-name Bitcoin.step2_approve_outputs
- shows the function on an object, with a definition
>>> get.py ELF_FILE --no-aggregation --no-sort --no-processing
- suppressing some actions
>>> get.py ELF_FILE -o result.txt
- output to a file
"""

from __future__ import annotations

from fnmatch import fnmatch

import click

from .. import BinarySize
from .build import build_binary


@click.command()
@click.argument("elf_file")
@click.option("-m", "--map-file", help="Path to map file")
@click.option(
    "-s", "--sections", multiple=True, help="Sections which to analyze. All if not set."
)
@click.option("-o", "--output-file", help="Dump results to file instead of stdout")
@click.option(
    "-l",
    "--language",
    help="Language choice - e.g. `Rust`",
)
@click.option(
    "-g",
    "--grep",
    help="Custom string to filter the row with, case-insensitive - e.g. `bitcoin`",
)
@click.option(
    "-M",
    "--module-name",
    "--mn",
    help="Check only specific file/module. Supports shell-style wildcards - e.g. `*/networks.py`",
)
@click.option(
    "-F",
    "--func-name",
    "--fn",
    help="Check only specific function - e.g. `get_tx_keys`",
)
@click.option("-b", "--build", is_flag=True, help="Perform build")
@click.option(
    "-d",
    "--add-definitions",
    "--ad",
    is_flag=True,
    help="Get line definitions for all functions",
)
@click.option(
    "-G",
    "--no-aggregation",
    "--na",
    is_flag=True,
    help="Do not aggregate symbols together",
)
@click.option("-S", "--no-sort", "--ns", is_flag=True, help="Do not sort by size")
@click.option("-P", "--no-processing", "--np", is_flag=True, help="See just raw data")
def get(
    elf_file: str,
    map_file: str | None,
    sections: list[str] | None,
    output_file: str,
    language: str,
    grep: str,
    module_name: str,
    func_name: str,
    build: bool,
    add_definitions: bool,
    no_processing: bool,
    no_sort: bool,
    no_aggregation: bool,
) -> None:
    """Analyze a single binary."""

    if build:
        build_binary()

    BS = BinarySize()

    BS.load_file(elf_file, sections=sections)

    if no_processing:
        return BS.show()

    if map_file and sections:
        BS.use_map_file(map_file, sections=sections)

    BS.add_basic_info()

    if not no_aggregation:
        BS.aggregate()
    if not no_sort:
        BS.sort(lambda row: row.size, reverse=True)

    if language:
        BS.filter(lambda row: row.language == language)
    if module_name:
        BS.filter(lambda row: fnmatch(row.module_name, module_name))
    if func_name:
        # There could be an object or not ... Bitcoin.sign_tx vs sign_tx
        # If not, we need to account for the possible object in row.func_name
        if "." in func_name:
            BS.filter(lambda row: row.func_name.rstrip("()") == func_name)
        else:
            BS.filter(
                lambda row: row.func_name.rstrip("()").split(".")[-1] == func_name
            )
    if grep:
        BS.filter(lambda row: grep.lower() in str(row).lower())

    if add_definitions:
        BS.add_definitions()

    if output_file:
        BS.show(output_file)
    else:
        BS.show()


if "__main__" == __name__:
    get()
