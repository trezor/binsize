#!/usr/bin/env python3
"""
Main object for analyzing the size of the binary.
Assembling all the smaller components together and exposing them.

By default works with `bloaty` - https://github.com/google/bloaty/
However, any other tool can be used (for example `nm`) - it is just
a matter of creating appropriate class implementing `api.RowDataLoaderAPI`.

Offers a lot of features, users can choose what exactly it will do.
They can also supply custom implementations of data processing
and data visualization.
See the `api.BinarySizeAPI` for full description.
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from itertools import count
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Sequence

from termcolor import cprint
from typing_extensions import Self

from ..user_data import cache_dir
from .api import BinarySizeAPI
from .build_definition_loader import BuildDefinitionLoader
from .common import ProgressBar
from .data_handler import RowHandlerFactory
from .data_loader import BloatyDataLoader
from .map_file_includer import MapFileIncluder
from .source_definition_cache import SourceDefinitionCache

if TYPE_CHECKING:  # pragma: no cover
    from .api import (
        BuildDefinitionLoaderAPI,
        DataRow,
        MapFileIncluderAPI,
        RowDataLoaderAPI,
        RowHandlerAPI,
    )

DEFINITIONS_CACHE_FILE = cache_dir / "DEFINITIONS_CACHE.json"


class BinarySize(BinarySizeAPI):
    NO_DATA_MSG = "There are no data. Call load_xxx() first."

    def __init__(
        self,
        data_loader: RowDataLoaderAPI = BloatyDataLoader(),
        row_handler_factory: Callable[[DataRow], RowHandlerAPI] = RowHandlerFactory(
            source_def_cache=SourceDefinitionCache(DEFINITIONS_CACHE_FILE)
        ),
        build_def_loader: BuildDefinitionLoaderAPI | None = BuildDefinitionLoader(),
    ):
        # Custom object for data loading
        self.data_loader = data_loader
        # Custom handler for data processing
        self.row_handler_factory = row_handler_factory
        # Optional object for getting build definitions from the binary file
        self.build_def_loader = build_def_loader
        # Data to work with - empty at the beginning, filled by load_XXX functions
        self.row_data: list[DataRow] | None = None
        # Whether some functions were already called - to hint users if they
        # could be calling functions in possibly "bad" order
        self.called_aggregate = False
        self.called_add_basic_info = False

    def load_file(
        self,
        bin_file: str | Path,
        sections: Sequence[str] | None = None,
    ) -> Self:
        return self._load(bin_file=bin_file, sections=sections)

    def load_csv(
        self,
        csv_output: str,
        sections: Sequence[str] | None = None,
    ) -> Self:
        return self._load(csv_output=csv_output, sections=sections)

    def load_data(
        self,
        row_data: list[DataRow],
    ) -> Self:
        return self._load(row_data=row_data)

    def aggregate(self) -> Self:
        assert self.row_data is not None, self.NO_DATA_MSG
        print("Aggregating data... Grouping common symbols together.")
        self.row_data = aggregate_rows(self.row_data)
        self.called_aggregate = True
        return self

    def sort(
        self,
        key: Callable[[DataRow], Any] = lambda row: row.size,
        reverse: bool = True,
    ) -> Self:
        assert self.row_data is not None, self.NO_DATA_MSG
        self.row_data.sort(key=key, reverse=reverse)
        return self

    def add_basic_info(self) -> Self:
        assert self.row_data is not None, self.NO_DATA_MSG
        print("Adding basic info... Resolving module and function names.")
        self.row_data = [
            self.row_handler_factory(row).add_basic_info(row) for row in self.row_data
        ]
        self.called_add_basic_info = True
        return self

    def add_definitions(
        self, condition: Callable[[DataRow], bool] | None = None
    ) -> Self:
        assert self.row_data is not None, self.NO_DATA_MSG
        print(
            "Adding definitions... This can take a long time if the results are not cached."
        )
        if not self.called_aggregate:
            cprint(
                "    WARNING: you might want to call aggregate() first\n"
                "             before adding definitions.\n"
                "             It will be much quicker.",
                color="red",
            )

        progress_bar = ProgressBar(len(self.row_data))
        progress_counter = count(start=1)

        def _include_definitions(row: DataRow) -> DataRow:
            progress_bar.update(next(progress_counter))
            if condition is not None and condition(row) is False:
                return row
            else:
                return self.row_handler_factory(row).add_definition(row)

        self.row_data = [_include_definitions(row) for row in self.row_data]
        return self

    def use_map_file(
        self,
        map_file: str | Path,
        sections: Sequence[str],
        map_includer_object: MapFileIncluderAPI = MapFileIncluder(),
    ) -> Self:
        assert self.row_data is not None, self.NO_DATA_MSG

        print(f"Including data from map file - {map_file}")
        if self.called_aggregate or self.called_add_basic_info:
            cprint(
                "    WARNING: you might want to call add_basic_info() and aggregate()\n"
                "             again after calling use_map_file().\n"
                "             That will sync up the old data and the new data.",
                color="red",
            )

        self.row_data = map_includer_object.add_info(self.row_data, map_file, sections)
        return self

    def filter(self, filter_func: Callable[[DataRow], bool]) -> Self:
        assert self.row_data is not None, self.NO_DATA_MSG
        self.row_data = [row for row in self.row_data if filter_func(row)]
        return self

    def get(self) -> list[DataRow]:
        assert self.row_data is not None, self.NO_DATA_MSG
        return self.row_data

    def get_size(self) -> int:
        assert self.row_data is not None, self.NO_DATA_MSG
        return sum(row.size for row in self.row_data)

    def _get_logic_size(self) -> int:
        assert self.row_data is not None, self.NO_DATA_MSG
        return sum(row.logic_size for row in self.row_data)

    def _get_data_size(self) -> int:
        assert self.row_data is not None, self.NO_DATA_MSG
        return sum(row.data_size for row in self.row_data)

    def get_len(self) -> int:
        assert self.row_data is not None, self.NO_DATA_MSG
        return len(self.row_data)

    def show(
        self,
        file_to_save: str | Path | None = None,
        debug: bool = False,
        row_data_formatter: Callable[[list[DataRow]], str] | None = None,
    ) -> None:
        assert self.row_data is not None, self.NO_DATA_MSG
        final_output = self._get_printable_output(
            is_file=file_to_save is not None,
            debug=debug,
            row_data_formatter=row_data_formatter,
        )

        if file_to_save:
            print(f"Saving report to {file_to_save}")
            with open(file_to_save, "w") as f:
                f.write(final_output)
        else:
            print(final_output)

    def _load(
        self,
        row_data: list[DataRow] | None = None,
        bin_file: str | Path | None = None,
        csv_output: str | None = None,
        sections: Sequence[str] | None = None,
    ) -> Self:
        assert self.row_data is None, "Data already loaded"
        assert (
            sum(bool(x) for x in (row_data, bin_file, csv_output)) == 1
        ), "only one load option can be specified"

        if row_data:
            self.row_data = row_data
            return self
        elif bin_file:
            self.row_data = self.data_loader.load_data_from_file(bin_file, sections)
            # Optionally including build definitions from the file
            if self.build_def_loader is not None:
                self.row_data = self._include_build_definitions(self.row_data, bin_file)
            return self
        elif csv_output:
            self.row_data = self.data_loader.load_data_from_csv(csv_output, sections)
            return self
        else:
            raise RuntimeError("No load option specified")

    def _get_printable_output(
        self,
        is_file: bool = False,
        debug: bool = False,
        row_data_formatter: Callable[[list[DataRow]], str] | None = None,
    ) -> str:
        assert self.row_data is not None
        if row_data_formatter is not None:
            return row_data_formatter(self.row_data)
        else:
            summary = self._get_data_summary()
            result_data = "\n".join(row.format(debug=debug) for row in self.row_data)
            # Putting summary at the most visible place - top for file, bottom for terminal
            return (
                f"{summary}\n{result_data}" if is_file else f"{result_data}\n{summary}"
            )

    def _get_data_summary(self) -> str:
        assert self.row_data is not None
        row_amount = self.get_len()
        overall_size = self.get_size()
        logic_size = self._get_logic_size()
        data_size = self._get_data_size()
        return f"SUMMARY: {row_amount:_} rows, {overall_size:_} bytes in total (L{logic_size:_} D{data_size:_})."

    def _include_build_definitions(
        self, row_data: list[DataRow], bin_file: str | Path
    ) -> list[DataRow]:
        """Adding build definitions to the rows from the binary file"""
        assert self.build_def_loader is not None
        self.build_def_loader.load(bin_file)

        for row in row_data:
            build_definition = self.build_def_loader.get(row.symbol_name)
            if build_definition is not None:
                row.build_definition = build_definition

        return row_data


def aggregate_rows(row_data: list[DataRow]) -> list[DataRow]:
    """There could be more entries belonging together, so aggregating them into one.

    Using DataRow.id() as the identifier for aggregation.
    """
    deduplication_dict: dict[str, list[DataRow]] = defaultdict(list)
    for row in row_data:
        deduplication_dict[row.id()].append(row)

    new_rows: list[DataRow] = []
    # Calculating the overall size of rows belonging together
    for alike_rows in deduplication_dict.values():
        new_row = deepcopy(alike_rows[0])  # apart from size, all rows are the same
        new_row.size = sum(row.size for row in alike_rows)
        new_row.logic_size = sum(row.logic_size for row in alike_rows)
        new_row.data_size = sum(row.data_size for row in alike_rows)
        new_row.number_of_symbols = len(alike_rows)
        new_rows.append(new_row)

    return new_rows
