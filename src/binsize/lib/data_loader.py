"""
Defining the data loaders.
All loaders must implement `api.RowDataLoaderAPI`.
"""

from __future__ import annotations

import csv
import subprocess
import sys
from io import StringIO
from pathlib import Path
from typing import Sequence, cast

from typing_extensions import TypedDict

from .api import DataRow, RowDataLoaderAPI


class BloatyRow(TypedDict):
    sections: str
    symbols: str
    vmsize: str
    filesize: str


class BloatyDataLoader(RowDataLoaderAPI):
    def __init__(self) -> None:
        pass

    def load_data_from_file(
        self, bin_file: str | Path, sections: Sequence[str] | None = None
    ) -> list[DataRow]:
        if not Path(bin_file).exists():
            raise FileNotFoundError(f"File {bin_file} does not exist")
        bloaty_cmd = f"bloaty -n 0 -d sections,symbols -s vm --csv {bin_file}"
        csv_output = self.get_csv_output(bloaty_cmd)
        return self.load_data_from_csv(csv_output, sections)

    @staticmethod
    def get_csv_output(bloaty_cmd: str) -> str:
        print(f"Running CMD: `{bloaty_cmd}`")
        result = subprocess.run(
            bloaty_cmd, stdout=subprocess.PIPE, text=True, shell=True
        )

        if result.returncode != 0:
            print("command failed, see output above")
            sys.exit(1)

        return result.stdout

    def load_data_from_csv(
        self, csv_output: str, sections: Sequence[str] | None = None
    ) -> list[DataRow]:
        csv_reader = csv.DictReader(StringIO(csv_output))
        bloaty_rows: list[BloatyRow] = [cast(BloatyRow, row) for row in csv_reader]

        if not sections:
            return self._get_row_data(bloaty_rows)
        else:
            relevant_bloaty_rows = [
                row for row in bloaty_rows if row["sections"] in sections
            ]
            return self._get_row_data(relevant_bloaty_rows)

    def _get_row_data(self, bloaty_rows: list[BloatyRow]) -> list[DataRow]:
        return [self._get_data_row_from_bloaty_row(row) for row in bloaty_rows]

    def _get_data_row_from_bloaty_row(self, bloaty_row: BloatyRow) -> DataRow:
        symbol_name = bloaty_row["symbols"]
        default_data_row = DataRow(
            symbol_name=symbol_name,
            section=bloaty_row["sections"],
            size=int(bloaty_row["filesize"]),
        )
        return default_data_row
