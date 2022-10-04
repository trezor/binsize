"""
Including information from map file.

It should cover at least some of the mysterious data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .api import DataRow, MapFileIncluderAPI
from .map_file_analyzer import get_section_data


class MapFileIncluder(MapFileIncluderAPI):
    def add_info(
        self, row_data: list[DataRow], map_file: str | Path, sections: Sequence[str]
    ) -> list[DataRow]:
        # Adding the info one section at a time
        for section in sections:
            map_symbol_sizes = get_symbol_sizes(map_file, section)
            map_symbols_we_miss = get_symbols_we_miss(
                row_data, map_symbol_sizes, section
            )
            added_size = add_map_file_info(
                row_data, map_symbol_sizes, map_symbols_we_miss, section
            )

            print(f"Added {added_size:_} bytes to {section} section from {map_file}")

            decrease_size_of_mysterious_section(row_data, section, added_size)

        return row_data


def get_symbol_sizes(map_file: str | Path, section: str) -> dict[str, int]:
    symbol_sizes: dict[str, int] = {}
    section_data = get_section_data(map_file, section)
    for symbol_name, symbol_entries in section_data.items():
        size = symbol_entries.total_size()
        # There are some symbols like ".bootloader" - just a section without any symbol
        # In all other cases getting rid of the section
        if symbol_name.count(".") < 2:
            symbol_sizes[symbol_name] = size
        else:
            no_section_name = symbol_name.lstrip(".").split(".", maxsplit=1)[-1]
            symbol_sizes[no_section_name] = size

    return symbol_sizes


def get_symbols_we_miss(
    row_data: list[DataRow], map_symbol_sizes: dict[str, int], section: str
) -> set[str]:
    our_symbols = set(row.symbol_name for row in row_data if row.section == section)
    map_symbols = set(symbol for symbol in map_symbol_sizes.keys())

    def _is_duplicate_rust_symbol(map_s: str) -> bool:
        # Rust symbols look little different in bloaty and map file
        # core::option::Option$LT$T$GT$::map_or_else::hee63c66131f899de vs
        # _ZN4core6option15Option<T>11map_or_else17hee63c66131f899deE
        # Checking if that end hash does not appear in our symbols already
        if not (map_s.startswith("_ZN") and map_s.endswith("E")):
            return False

        end_hash = map_s[-10:-1]
        for row in row_data:
            if row.symbol_name.endswith(end_hash):
                return True
        return False

    def _symbol_is_missing(map_s: str) -> bool:
        if map_s in our_symbols:
            return False
        if _is_duplicate_rust_symbol(map_s):
            return False
        return True

    return {map_s for map_s in map_symbols if _symbol_is_missing(map_s)}


def add_map_file_info(
    row_data: list[DataRow],
    map_symbol_sizes: dict[str, int],
    map_symbols_we_miss: set[str],
    section: str,
) -> int:
    added_size = 0
    for missing_symbol in map_symbols_we_miss:
        symbol_size = map_symbol_sizes[missing_symbol]
        row_data.append(
            DataRow(
                symbol_name=missing_symbol,
                section=section,
                size=symbol_size,
            )
        )
        added_size += symbol_size

    return added_size


def decrease_size_of_mysterious_section(
    row_data: list[DataRow], section: str, added_size: int
) -> None:
    # Decreasing the "mysterious" symbol data by what we have added
    section_symbol = f"[section {section}]"
    for row in row_data:
        if row.symbol_name == section_symbol:
            row.size -= added_size
            print(f"Decreasing the size of `{section_symbol}` by {added_size:_} bytes")
            break
    else:
        print(f"WARNING: could not decrease the size of `{section_symbol}`")
