from __future__ import annotations

import re

from binsize.lib.api import DataRow
from binsize.plugins.statistics import CategoryStatistics, StatisticsPlugin

from .common import get_bloaty_BS, mock_data_row

APP_DATA = [
    mock_data_row(module_name="src/apps/ethereum/gfdg/fdasdas.py", size=222),
    mock_data_row(module_name="src/apps/ethereum/dac/das.py", size=222),
    mock_data_row(module_name="src/apps/nem/dfgcx/tergdf.py", size=333),
    mock_data_row(module_name="src/apps/nem/def/asd.py", size=333),
    mock_data_row(module_name="src/apps/nem/dsa/AS.py", size=333),
    mock_data_row(module_name="src/apps/bitcoin/cagd/fgscxz.py", size=444),
    mock_data_row(module_name="src/apps/bitcoin/das/aS.py", size=444),
    mock_data_row(module_name="src/apps/bitcoin/fsdf/das.py", size=444),
    mock_data_row(module_name="src/apps/bitcoin/ghi/vcxvxc.py", size=444),
    mock_data_row(module_name="vendor/monero/dac/das.py", size=999),
    mock_data_row(module_name="embed/ripple/dac/das.py", size=999),
    mock_data_row(module_name="lalala/src/apps/musilcoin/dac/das.py", size=999),
]
APP_CATEGORIES = [
    "ethereum",
    "ethereum",
    "nem",
    "nem",
    "nem",
    "bitcoin",
    "bitcoin",
    "bitcoin",
    "bitcoin",
    None,
    None,
    None,
]


def apps_categories(row: DataRow) -> str | None:
    pattern = r"^src/apps/(\w+)/"
    match = re.search(pattern, row.module_name)
    if not match:
        return None
    else:
        return match.group(1)


def test_get_all_categories_apps():
    BS = get_bloaty_BS().load_data(APP_DATA)
    assert StatisticsPlugin(BS, apps_categories)._get_all_categories() == set(
        ["nem", "ethereum", "bitcoin", None]
    )


def test_include_category_data():
    BS = get_bloaty_BS().load_data(APP_DATA)
    SP = StatisticsPlugin(BS, apps_categories)
    for index, row in enumerate(SP.row_data_with_category):
        assert row.data_row == APP_DATA[index]
        assert row.category == APP_CATEGORIES[index]


def test_get_categories_statistics():
    BS = get_bloaty_BS().load_data(APP_DATA)
    SP = StatisticsPlugin(BS, apps_categories)
    assert SP._get_categories_statistics() == [
        CategoryStatistics(category=None, size=3 * 999, symbol_amount=3),
        CategoryStatistics(category="bitcoin", size=4 * 444, symbol_amount=4),
        CategoryStatistics(category="nem", size=3 * 333, symbol_amount=3),
        CategoryStatistics(category="ethereum", size=2 * 222, symbol_amount=2),
    ]
