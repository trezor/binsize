from __future__ import annotations

import pytest

from binsize import settings
from binsize.lib.map_file_includer import (
    add_map_file_info,
    decrease_size_of_mysterious_section,
    get_symbol_sizes,
    get_symbols_we_miss,
)

from .common import mock_data_row

ROW_DATA = [
    mock_data_row(section=".flash", symbol_name="[section .flash]", size=14),
    mock_data_row(section=".flash", symbol_name="aaa", size=2),
    mock_data_row(section=".flash", symbol_name="bbb", size=2),
    mock_data_row(section=".flash", symbol_name="ccc", size=2),
    mock_data_row(section=".flash", symbol_name="ddd", size=2),
    mock_data_row(
        section=".flash",
        symbol_name="core::option::Option$LT$T$GT$::map_or_else::hee63c66131f899de",
        size=4,
    ),
    mock_data_row(section=".flash2", symbol_name="[section .flash2]", size=14),
    mock_data_row(section=".flash2", symbol_name="eee", size=2),
    mock_data_row(section=".flash2", symbol_name="fff", size=2),
]
MAP_SYMBOL_SIZES = {
    "aaa": 1,
    "bbb.str1.1": 2,
    "zzz": 3,
    "_ZN4core6option15Option<T>11map_or_else17hee63c66131f899deE": 4,
}


def test_load_map_file():
    if not settings.MAP_FILE.exists():
        pytest.fail(f"{settings.MAP_FILE} not found")
    res = get_symbol_sizes(settings.MAP_FILE, section=".flash")
    assert len(res) > 1000
    assert sum(res.values()) > 100_000


def test_get_symbols_we_miss():
    res = get_symbols_we_miss(ROW_DATA, MAP_SYMBOL_SIZES, section=".flash")
    assert res == set(["bbb.str1.1", "zzz"])


def test_add_map_file_info():
    map_symbols_we_miss = set(["bbb.str1.1", "zzz"])
    row_data = ROW_DATA.copy()
    assert len(row_data) == 9
    res = add_map_file_info(
        row_data, MAP_SYMBOL_SIZES, map_symbols_we_miss, section=".flash"
    )
    assert res == 5
    assert len(row_data) == 11
    old_ones = row_data[:9]
    assert old_ones == ROW_DATA
    new_ones = sorted(row_data[9:], key=lambda x: x.symbol_name)
    assert new_ones == [
        mock_data_row(section=".flash", symbol_name="bbb.str1.1", size=2),
        mock_data_row(section=".flash", symbol_name="zzz", size=3),
    ]


def test_decrease_size_of_mysterious_section():
    row_data = ROW_DATA.copy()
    assert len(row_data) == 9
    decrease_size_of_mysterious_section(row_data, section=".flash", added_size=5)
    assert len(row_data) == 9
    assert row_data[0] == mock_data_row(
        section=".flash", symbol_name="[section .flash]", size=14 - 5
    )
    assert row_data[1:] == ROW_DATA[1:]
