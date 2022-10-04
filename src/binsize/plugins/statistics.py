"""
Groups data into categories and returns statistics about each category.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:  # pragma: no cover
    from ..lib.api import BinarySizeAPI, DataRow


@dataclass
class CategoryStatistics:
    category: str | None
    size: int
    symbol_amount: int

    def format(self) -> str:
        return f"{self.size:>10_}: {str(self.category):<20} ({self.symbol_amount:>5_} symbols)"


@dataclass
class CategoryRow:
    category: str | None
    data_row: DataRow

    def format(self) -> str:
        return f"{str(self.category):<15}: {self.data_row.format()}"


class StatisticsPlugin:
    def __init__(
        self,
        binary_size: BinarySizeAPI,
        categories_func: Callable[[DataRow], str | None],
    ):
        self.binary_size = binary_size
        # Function that takes a row and returns a string, that will be
        # used as a category for the row. Returns None if no category matches.
        self.categories_func = categories_func
        self.row_data_with_category = self._include_category_data()

    def get(self) -> list[CategoryStatistics]:
        return self._get_categories_statistics()

    def show_data_with_categories(
        self, file_to_save: str | Path | None = None, include_none: bool = False
    ) -> None:
        final_output = "\n".join(
            category_row.format() for category_row in self.row_data_with_category
        )

        _show(final_output, file_to_save)

    def show(
        self,
        file_to_save: str | Path | None = None,
        include_none: bool = False,
        include_categories_func: bool = False,
    ) -> None:
        statistics_data = self._get_categories_statistics()
        final_output = _get_printable_output(
            statistics_data, is_file=file_to_save is not None, include_none=include_none
        )

        # Optionally including the categories function definition for
        # documentation and replication purposes
        if include_categories_func:
            final_output = f"{inspect.getsource(self.categories_func)}\n{final_output}"

        _show(final_output, file_to_save)

    def _include_category_data(self) -> list[CategoryRow]:
        return [
            CategoryRow(category=self.categories_func(row), data_row=row)
            for row in self.binary_size.get()
        ]

    def _get_all_categories(self) -> set[str | None]:
        return set([row.category for row in self.row_data_with_category])

    def _get_categories_statistics(self) -> list[CategoryStatistics]:
        all_categories: list[CategoryStatistics] = []
        for category in self._get_all_categories():
            all_category_items = [
                row for row in self.row_data_with_category if row.category == category
            ]
            all_categories.append(
                CategoryStatistics(
                    category=category,
                    size=sum(row.data_row.size for row in all_category_items),
                    symbol_amount=len(all_category_items),
                )
            )

        all_categories.sort(key=lambda x: x.size, reverse=True)
        return all_categories


def _show(final_output: str, file_to_save: str | Path | None = None) -> None:
    if file_to_save:
        print(f"Saving statistics report to {file_to_save}")
        with open(file_to_save, "w") as f:
            f.write(final_output)
    else:
        print(final_output)


def _get_printable_output(
    statistics_data: list[CategoryStatistics],
    include_none: bool = False,
    is_file: bool = False,
) -> str:
    if not include_none:
        # Getting rid of the empty category
        statistics_data = [row for row in statistics_data if row.category is not None]
    summary = _get_data_summary(statistics_data)
    result_data = "\n".join(row.format() for row in statistics_data)
    # Putting summary at the most visible place - top for file, bottom for terminal
    return f"{summary}\n{result_data}" if is_file else f"{result_data}\n{summary}"


def _get_data_summary(statistics_data: list[CategoryStatistics]) -> str:
    category_amount = len(statistics_data)
    overall_size = sum(row.size for row in statistics_data)
    symbol_count = sum(row.symbol_amount for row in statistics_data)
    return f"SUMMARY: {category_amount:_} categories, {symbol_count:_} symbols, {overall_size:_} bytes in total."
