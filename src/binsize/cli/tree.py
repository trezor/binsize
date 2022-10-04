from __future__ import annotations

import click

from .. import BinarySize, SizeTreePlugin


@click.command()
@click.argument("fw_location", required=True)
@click.option("-m", "--map-file", help="Path to map file")
@click.option(
    "-s", "--sections", multiple=True, help="Sections which to analyze. All if not set."
)
def tree(fw_location: str, map_file: str | None, sections: list[str]) -> None:
    """Get file-tree view of binary size."""
    print(f"Analyzing {fw_location}")

    BS = BinarySize().load_file(fw_location, sections=sections)

    if map_file and sections:
        BS.use_map_file(map_file, sections=sections)

    BS.add_basic_info().aggregate().add_definitions()

    SizeTreePlugin(BS).show()


if __name__ == "__main__":
    tree()
