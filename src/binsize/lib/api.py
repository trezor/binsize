"""
Defining all the interfaces between components.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol, Sequence

from typing_extensions import Self


@dataclass
class DataRow:
    # Initial info, coming directly from `RowDataLoader`
    symbol_name: str
    section: str
    size: int

    # Added optionally by `RowHandler.add_basic_info`
    language: str = ""
    func_name: str = ""  # possibly including an object
    module_name: str = ""  # file from where the symbol comes from
    logic_size: int = 0  # how much of the symbol size is logic
    data_size: int = 0  # how much of the symbol size is data

    # Added optionally by `BuildDefinitionLoader`
    build_definition: str = ""  # definition which goes to the build

    # Added optionally by `BinarySize.aggregate`
    number_of_symbols: int = 0  # how many symbols are aggregated under one

    # Added optionally by `RowHandler.add_source_definition`
    # In case of C files, this definition is the same as the build definition
    # In case of micropython, build definition points to `build/firmware/frozen_mpy.c`,
    # but source definition will be somewhere in src/apps/
    # Rust files do not even have the build definition, searching for
    # source definition in `embed/rust/src`
    source_definition: str = ""  # definition in the source file

    def id(self) -> str:
        """Identifying this row"""
        # Used when aggregating alike rows together
        # Each non-alike row should be always unique, even when no basic info is filled
        # Need to include a section, not to mix same-named items from different sections
        def _name_id() -> str:
            if self.module_name and self.func_name:
                return f"{self.module_name}::{self.func_name}"
            elif self.module_name:
                return self.module_name
            elif self.func_name:
                return self.func_name
            else:
                return self.symbol_name

        return f"{self.section}_{_name_id()}"

    def format(self, debug: bool = False) -> str:
        """Nicely formatting this row"""
        # Definition might not be filled, but when it is, show it instead of the module name
        # Also, the module name and function name can be empty
        # Default to symbol name, which is always there
        if self.source_definition:
            name_to_show = f"{self.source_definition:<60} {self.func_name}"
        elif self.module_name:
            name_to_show = f"{self.module_name:<60} {self.func_name}"
        elif self.func_name:
            name_to_show = self.func_name
        else:
            name_to_show = self.symbol_name

        to_show = f"{self.section:<10} {self.size:<7_} {self.number_of_symbols:<4} L{self.logic_size:<7_} D{self.data_size:<7_}"
        if debug:
            # Optionally showing also the raw symbol name
            return f"{to_show} {name_to_show:<100} {self.symbol_name}"
        else:
            return f"{to_show} {name_to_show}"


class RowHandlerAPI(Protocol):
    """Responsible for handling the row data"""

    language: str

    def add_basic_info(self, row: DataRow) -> DataRow:
        """Fill in some info, like the module name and the function name."""
        ...  # pragma: no cover

    def add_definition(self, row: DataRow) -> DataRow:
        """Include the place where the symbol is defined, if possible."""
        ...  # pragma: no cover


class RowDataLoaderAPI(Protocol):
    """Resposible for loading the row data from some sources."""

    def load_data_from_file(
        self, bin_file: str | Path, sections: Sequence[str] | None = None
    ) -> list[DataRow]:
        """Analyse a file and return basic DataRow objects."""
        ...  # pragma: no cover

    def load_data_from_csv(
        self, csv_output: str, sections: Sequence[str] | None = None
    ) -> list[DataRow]:
        """Return basic DataRow objects based on CSV output."""
        ...  # pragma: no cover


class SourceDefinitionCacheAPI(Protocol):
    """Resposible for keeping expensive-to-compute line definitions."""

    def add(self, symbol: str, definition: str) -> None:
        """Include/update a definition for a symbol."""
        ...  # pragma: no cover

    def get(self, symbol: str) -> str | None:
        """Retrieve definition for a symbol. Return None if not found."""
        ...  # pragma: no cover

    def is_invalidated(self, symbol: str) -> bool:
        """Whether definition for this symbol is not valid anymore."""
        ...  # pragma: no cover


class BuildDefinitionLoaderAPI(Protocol):
    """Responsible for getting all available definition data in the binary."""

    def load(self, bin_file: str | Path) -> None:
        """Load build definitions from binary."""
        ...  # pragma: no cover

    def get(self, symbol_name: str) -> str | None:
        """Return build definition for a symbol."""
        ...  # pragma: no cover


class MapFileIncluderAPI(Protocol):
    """Responsible for including "missing/mysterious" data from map file."""

    def add_info(
        self, row_data: list[DataRow], map_file: str | Path, sections: Sequence[str]
    ) -> list[DataRow]:
        """Adds map file info to existing data."""
        ...  # pragma: no cover


class BinarySizeAPI(Protocol):
    """Highest level component, putting everything together and exposing it."""

    def load_file(
        self,
        bin_file: str | Path,
        sections: Sequence[str] | None = None,
    ) -> Self:
        """Load data from analysis of a binary file."""
        ...  # pragma: no cover

    def load_csv(
        self,
        csv_output: str,
        sections: Sequence[str] | None = None,
    ) -> Self:
        """Load data from a CSV output string."""
        ...  # pragma: no cover

    def load_data(
        self,
        row_data: list[DataRow],
    ) -> Self:
        """Load already existing row data."""
        ...  # pragma: no cover

    def aggregate(self) -> Self:
        """Aggregate all the symbols belonging together into one row."""
        ...  # pragma: no cover

    def add_basic_info(self) -> Self:
        """Include the quick-to-get basic info about each row."""
        ...  # pragma: no cover

    def add_definitions(
        self, condition: Callable[[DataRow], bool] | None = None
    ) -> Self:
        """Include the definition for all rows matching an optional condition.

        NOTE: will also call add_basic_info() if not already called,
        as it needs that information to create a definition.

        WARNING: can be quite time-consuming if called on big amount of rows.
        Use the optional `condition` function to narrow the scope, if needed.
        """
        ...  # pragma: no cover

    def filter(self, filter_func: Callable[[DataRow], bool]) -> Self:
        """Filters the data rows according to some filter function."""
        ...  # pragma: no cover

    def sort(self, key: Callable[[DataRow], Any], reverse: bool = False) -> Self:
        """Sorts the data according to arbitrary function."""
        ...  # pragma: no cover

    def get(self) -> list[DataRow]:
        """Return all the internally processed data rows."""
        ...  # pragma: no cover

    def get_size(self) -> int:
        """Get the overall size of the rows."""
        ...  # pragma: no cover

    def get_len(self) -> int:
        """Get the number of rows."""
        ...  # pragma: no cover

    def show(
        self,
        file_to_save: str | Path | None = None,
        debug: bool = False,
        row_data_formatter: Callable[[list[DataRow]], str] | None = None,
    ) -> None:
        """Output the results in a stringified format - to file or stdout.

        Offers to supply own data formatter responsible for stringifying the data.
        """
        ...  # pragma: no cover
