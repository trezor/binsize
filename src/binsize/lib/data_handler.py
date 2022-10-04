"""
Defining factory for all the data handlers.
All handlers must implement `api.RowHandlerAPI`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .row_handler_c import CRow
from .row_handler_common import MPY_PREFIXES, RUST_PREFIXES
from .row_handler_mpy import MicropythonRow
from .row_handler_rust import RustRow

if TYPE_CHECKING:  # pragma: no cover
    from .api import DataRow, RowHandlerAPI
    from .source_definition_cache import SourceDefinitionCache


class RowHandlerFactory:
    def __init__(self, source_def_cache: SourceDefinitionCache | None = None) -> None:
        self.source_def_cache = source_def_cache

    def __call__(self, row: DataRow) -> RowHandlerAPI:
        """Choose appropriate row handler for given row."""
        # Some rust functions look like C ones, but are defined in "/cargo/..."
        if row.symbol_name.startswith(RUST_PREFIXES) or row.build_definition.startswith(
            "/cargo/"
        ):
            return RustRow(self.source_def_cache)
        elif row.symbol_name.startswith(MPY_PREFIXES):
            return MicropythonRow(self.source_def_cache)
        else:
            return CRow(self.source_def_cache)
