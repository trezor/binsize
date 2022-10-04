"""
Some generally useful things.
"""

from __future__ import annotations

import atexit
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Callable, TypeVar

if TYPE_CHECKING:
    R = TypeVar("R")


def file_cache(
    file_name: str | Path,
) -> Callable[[Callable[[str], R]], Callable[[str], R]]:
    """Decorator to cache the results of a function to a file.

    (Storing key-value pairs persistently.)
    Type hints make sure it can be used with any type of values
    (as long as they are valid JSON).
    Keys must be strings, as JSON does not support anything else.
    Decorated function also needs to have only one (string) argument.
    """
    try:
        cache: dict[str, R] = json.load(open(file_name, "r"))
    except (IOError, ValueError):
        cache = {}

    atexit.register(lambda: json.dump(cache, open(file_name, "w"), indent=4))

    def decorator(func: Callable[[str], R]) -> Callable[[str], R]:
        def new_func(param: str) -> R:
            if param not in cache:
                cache[param] = func(param)
            return cache[param]

        return new_func

    return decorator


class ProgressBar:
    """Simple progress bar.

    More suitable for our purposes than `click.progressbar`,
    because of its flexibility - no need to use it in `with` statement.
    """

    def __init__(self, total_amount: int, bar_length: int = 50) -> None:
        self.total_amount = total_amount
        self.bar_length = bar_length
        self.percents_previous = -1

    def update(self, count: int) -> None:
        percents = int(100.0 * count / self.total_amount)

        # Not updating if the percentage has not changed
        if percents == self.percents_previous:
            return
        self.percents_previous = percents

        filled_length = int(self.bar_length * percents / 100)
        bar = "#" * filled_length + "-" * (self.bar_length - filled_length)

        # [###-----------------------------------------------] 6% ... 3/50
        sys.stdout.write(f"\r[{bar}] {percents}% ... {count}/{self.total_amount}")
        if count == self.total_amount:
            sys.stdout.write("\n")
        sys.stdout.flush()
