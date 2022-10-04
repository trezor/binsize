"""
Some short useful functions being used in other scripts/CLI tools.
"""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import Sequence

from .lib.binary_size import BinarySize
from .lib.data_loader import BloatyDataLoader


def get_sections_sizes(
    bin_file: str | Path, sections: Sequence[str] | None
) -> dict[str, int]:
    bloaty_cmd = f"bloaty --csv {bin_file}"
    csv_output = BloatyDataLoader().get_csv_output(bloaty_cmd)

    csv_reader = csv.DictReader(StringIO(csv_output))
    result = {row["sections"]: int(row["filesize"]) for row in csv_reader}
    if sections:
        result = {section: result[section] for section in sections}
    return result


def show_binaries_diff(
    old: str | Path,
    new: str | Path,
    all_details: bool = False,
    sections: Sequence[str] | None = None,
    file_to_save: str | Path | None = None,
) -> None:
    bloaty_cmd = f"bloaty -n 0 -d sections,symbols --csv {new} -- {old}"
    csv_output = BloatyDataLoader().get_csv_output(bloaty_cmd)

    BS = (
        BinarySize()
        .load_csv(csv_output, sections=sections)
        .add_basic_info()
        .aggregate()
        .sort(lambda row: row.size, reverse=True)
    )

    if all_details:
        BS.add_definitions()

    BS.show(file_to_save)
