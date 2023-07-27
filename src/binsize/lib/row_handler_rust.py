"""
Defining handler logic for the Rust rows.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from .. import settings
from .row_handler_common import INVALID_FILE_PREFIX, CommonRow

if TYPE_CHECKING:  # pragma: no cover
    from .api import DataRow
    from .source_definition_cache import SourceDefinitionCache


class RustRow(CommonRow):
    language = "Rust"

    def __init__(self, source_def_cache: SourceDefinitionCache | None = None) -> None:
        super().__init__(source_def_cache)

    def _is_data(self, row: DataRow) -> bool:
        # In Rust there is no data, only logic
        return False

    def _get_module_and_function(self, symbol_name: str) -> tuple[str, str]:
        # It usually ends with a strange hex and might have dollars inside
        symbol_name = get_rid_of_hex_suffix(symbol_name)
        symbol_name = replace_dollar_encodings(symbol_name)

        # There might be some C-like symbols, for example
        # _ZN17compiler_builtins4math4libm5fmodf5fmodf17h71a899fe9710a6bdE coming from
        # /cargo/registry/src/github.com-1ecc6299db9ec823/compiler_builtins-0.1.53/src/../libm/src/math/fmodf.rs:5
        if "::" not in symbol_name:
            return "", symbol_name

        # Some symbols need different treatment - those being
        # somehow aliased to other symbols
        if symbol_name.startswith("_"):
            symbol_name = get_real_symbol_from_alias(symbol_name)

        # Split between our trezor_lib and other Rust stuff (core::xxx...)
        # Do not completely resolve the Rust things, as they are not in our source code
        if symbol_name.startswith("trezor_lib::"):
            return resolve_trezorlib_symbol(symbol_name)
        else:
            return "", f"{symbol_name}()"

    def _get_definition(self, row: DataRow) -> str:
        # If there is only a module, no need to locate any function definition
        # If not the module, no point in continuing either
        if not row.func_name:
            return row.module_name
        if not row.module_name:
            return ""

        line_num = get_line_num(row.module_name, row.func_name)
        if line_num:
            return f"{row.module_name}:{line_num}"
        else:
            return ""


def resolve_trezorlib_symbol(symbol_name: str) -> tuple[str, str]:
    items = symbol_name.split("::")

    # Filtering nonrelevant/strange items from there
    items = filter_nonrelevant_items(items)

    # There could be nothing left - leave it unrecognized
    if len(items) < 2:
        return "", ""

    # Removing the first item - trezor_lib
    items = items[1:]

    # Function and possible struct are at the end
    function_name = items.pop()
    if items[-1][0].isupper() or items[-1][0] == "_":
        struct_name = items.pop()
    else:
        struct_name = ""

    file_path = "embed/rust/src"
    for item in items:
        file_path += f"/{item}"

    if Path(settings.ROOT_DIR / f"{file_path}.rs").exists():
        file_path = f"{file_path}.rs"
    else:
        # could be that it points to mod.rs
        mod_file_path = f"{file_path}/mod.rs"

        if Path(settings.ROOT_DIR / mod_file_path).exists():
            file_path = mod_file_path
        else:
            file_path = f"{INVALID_FILE_PREFIX}{file_path}.rs"

    if struct_name:
        struct_and_function = f"{struct_name}::{function_name}()"
    else:
        struct_and_function = f"{function_name}()"

    return file_path, struct_and_function


def get_line_num(module_name: str, func_name: str) -> str:
    module_location = settings.ROOT_DIR / module_name
    func_name = func_name.replace("()", "").split("::")[-1]

    to_search = f"fn {func_name}[(<]"
    cmd = f'grep -m1 -n0 "{to_search}" {module_location} | cut -d: -f1'

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        shell=True,
    ).stdout.strip()
    return result


def replace_dollar_encodings(symbol_name: str) -> str:
    REPLACEMENTS = {
        "$LT$": "<",
        "$GT$": ">",
        "$RF$": "&",
        "$C$": ",",
        "..": "::",
    }

    for key, value in REPLACEMENTS.items():
        symbol_name = symbol_name.replace(key, value)

    # There could be many unicode characters (" ", "[", "}", etc.)
    # encoded as "$u20$", "$u5b$", etc.

    def _replace_unicode(match: re.Match[str]) -> str:
        unicode_num = match.group(1)
        try:
            return chr(int(unicode_num, 16))
        except ValueError:
            return match.group(0)

    return re.sub(r"\$u(\w\w)\$", _replace_unicode, symbol_name)


def get_real_symbol_from_alias(symbol_name: str) -> str:
    func_name = symbol_name.split(">::")[-1]

    # "_<...>::func_name" -> "..."
    symbol_name = symbol_name[2:]
    symbol_name = symbol_name[: -(len(func_name) + 3)]

    # Taking the rightmost symbol (no "&mut" etc)
    possibilities = [part.split()[-1] for part in symbol_name.split(" as ")]

    # Taking the left one when it is a valid symbol (not just a name),
    # otherwise the right one
    if len(possibilities) == 1 or "::" in possibilities[0]:
        symbol_name = possibilities[0]
    else:
        symbol_name = possibilities[1]

    return f"{symbol_name}::{func_name}"


def filter_nonrelevant_items(items: list[str]) -> list[str]:
    new_items: list[str] = []

    # There are some parts inside that we should not include
    should_keep = True

    for item in items:
        if item == "_{{closure}}":
            continue

        # Things like TYPE, which is a variable inside a function
        if all(char.isupper() for char in item):
            continue

        # Not interested in middle internal sequences like
        # "xxx::xxx::_<impl xxx::xxx>::xxx"
        if item.startswith("_<"):
            should_keep = False
        if not should_keep and item.endswith(">"):
            should_keep = True
            continue

        if should_keep:
            new_items.append(item)

    return new_items


def get_rid_of_hex_suffix(name: str) -> str:
    # If there is a hex suffix, get rid of it
    # Doing that to improve readability and also to match the possibly
    # duplicated functions once being in "+" and once in "-", just with
    # different suffixes
    hex_length = 16
    try:
        int(name[-hex_length:].lower(), 16)
        without_hex = name[:-hex_length]
        # Also possibly get rid of ending "::h"
        if without_hex.endswith("::h"):
            return without_hex[:-3]
        else:
            return without_hex
    except ValueError:
        return name
