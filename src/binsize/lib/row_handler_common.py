"""
Common things for all the row handlers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .api import RowHandlerAPI

if TYPE_CHECKING:  # pragma: no cover
    from .api import DataRow, SourceDefinitionCacheAPI

INVALID_FILE_PREFIX = "--invalid_file--"

# Defining all the prefixes here at one place,
# so we see they are not clashing with each other
MPY_PREFIXES = ("fun_data_", "const_table_data_", "const_obj_", "raw_code_")
RUST_PREFIXES = (
    "trezor_lib",
    "compiler_builtins",
    "core::",
    "_$LT$",
    "heapless::",
    "cstr_core::",
    "_ZN",
    "unlikely._ZN",
)


class CommonRow(RowHandlerAPI):
    """Common functionality for all the handlers.

    Provides a sensible implementation of the `RowHandlerAPI` that can be reused -
    _get_module_and_function(), _get_definition() and _is_data() are the only methods
    that need to be defined on the specific row handlers.
    """

    language = "Common language"

    def __init__(
        self, source_def_cache: SourceDefinitionCacheAPI | None = None
    ) -> None:
        self.source_def_cache = source_def_cache

    def add_basic_info(self, row: DataRow) -> DataRow:
        row.language = "" if row.symbol_name.startswith("[section") else self.language
        row.module_name, row.func_name = self._get_module_and_function(row.symbol_name)

        # Differentiating between logic and data
        # There are some special cases which we know are data
        if "str1.1" in row.symbol_name or ".rodata" in row.symbol_name:
            row.data_size = row.size
        elif self._is_data(row):
            row.data_size = row.size
        else:
            row.logic_size = row.size

        return row

    def add_definition(self, row: DataRow) -> DataRow:
        # In case row is missing a basic info, add it first
        if not row.language:
            row = self.add_basic_info(row)

        # Some special symbols do not need/have definition
        # e.g. [section .flash], .bootloader and other special symbols
        if (
            row.symbol_name.startswith("[")
            or row.symbol_name.startswith(".")
            or row.symbol_name.startswith("str1")
            or not row.symbol_name
        ):
            return row

        # Taking the source definition from the build definition, if
        # it is already there and is a valid source - not coming from build
        # (applicable for most of the C files)
        if (
            row.build_definition
            and "build/firmware/frozen_mpy.c" not in row.build_definition
        ):
            row.source_definition = row.build_definition
        else:
            row.source_definition = self._get_definition_cached(row)

        return row

    def _get_definition_cached(self, row: DataRow) -> str:
        if self.source_def_cache is not None:
            # If not in cache or invalidated, computing it and adding it to the cache
            cached = self.source_def_cache.get(row.symbol_name)
            if cached is None or self.source_def_cache.is_invalidated(row.symbol_name):
                result = self._get_definition(row)
                self.source_def_cache.add(row.symbol_name, result)
                return result
            else:
                return cached
        else:
            return self._get_definition(row)

    def _get_module_and_function(self, symbol_name: str) -> tuple[str, str]:
        ...

    def _get_definition(self, row: DataRow) -> str:
        ...

    def _is_data(self, row: DataRow) -> bool:
        ...
