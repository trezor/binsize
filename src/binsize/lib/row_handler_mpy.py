"""
Defining handler logic for the micropython rows.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from .. import settings
from .row_handler_common import INVALID_FILE_PREFIX, MPY_PREFIXES, CommonRow

if TYPE_CHECKING:  # pragma: no cover
    from .api import DataRow
    from .source_definition_cache import SourceDefinitionCache


@dataclass
class ObjectDefinition:
    """Enables searching for functions and classes in modules.

    Also used for resolving the symbol name - translating that
    into a series of classes and functions.
    """

    name: str
    # recursive objects, they can have infinite sub-objects
    functions: list[ObjectDefinition]
    classes: list[ObjectDefinition]
    start_line: int
    end_line: int

    # Classes interaction
    def has_top_level_class(self, cls_name: str) -> bool:
        """Check if given class name is a top-level class."""
        return cls_name in self.class_names()

    def class_names(self) -> list[str]:
        """Return all class names at this level."""
        return [cls.name for cls in self.classes]

    def get_class(self, cls_name: str) -> ObjectDefinition | None:
        """Return class definition if it exists."""
        for cls in self.classes:
            if cls.name == cls_name:
                return cls
        return None

    # Functions interaction
    def has_top_level_func(self, func_name: str) -> bool:
        """Check if given func name is a top-level function."""
        return func_name in self.func_names()

    def func_names(self) -> list[str]:
        """Return all function names at this level."""
        return [func.name for func in self.functions]

    def get_func(self, func_name: str) -> ObjectDefinition | None:
        """Return function definition if it exists."""
        for func in self.functions:
            if func.name == func_name:
                return func
        return None

    # Symbol resolving
    def resolve_symbol(self, symbol_name: str) -> str:
        """Get the function name of the symbol"""
        # First trying to match the top-level functions
        if symbol_name in self.func_names():
            return f"{symbol_name}()"

        # When not found, we need to find some combinations of
        # classes and functions that work together to assemble that symbol
        symbol_split = symbol_name.split("_")

        # Goal is the same for both the classes and functions:
        # - find longest possible part that is defined on top level
        # When class is found, continue resolving in that class
        # and separate classes with "."
        # When function is found, we have reached the end and return
        # the name with "()".
        # NOT resolving the function completely, just returning the
        # most top-level one (not to have so many individual objects)

        # Look into classes
        for i in range(len(symbol_split), 0, -1):
            class_try = "_".join(symbol_split[:i])
            if self.has_top_level_class(class_try):
                rest_of_symbol = "_".join(symbol_split[i:])
                new_class_object = self.get_class(class_try)
                assert new_class_object is not None
                new_resolved_symbol = new_class_object.resolve_symbol(rest_of_symbol)
                # Not generating a trailing dot when nothing follows
                if new_resolved_symbol:
                    return f"{class_try}.{new_resolved_symbol}"
                else:
                    return class_try

        # Look into functions
        for i in range(len(symbol_split), 0, -1):
            func_try = "_".join(symbol_split[:i])
            if self.has_top_level_func(func_try):
                return f"{func_try}()"

        return ""

    # Line number retrieving
    def get_line_number(self, func_name: str) -> int:
        """Get line number from the function declaration"""
        # Function has the same structure as coming from `resolve_symbol()`,
        # so checking for the objects and functions
        # Returning when done iterating through all substrings
        # Returning 0 on any mismatch as a sign of error
        current_object = self
        for symbol in func_name.split("."):
            assert current_object is not None
            if symbol.endswith("()"):
                if not current_object.has_top_level_func(symbol[:-2]):
                    return 0
                current_object = current_object.get_func(symbol[:-2])
            else:
                if not current_object.has_top_level_class(symbol):
                    return 0
                current_object = current_object.get_class(symbol)

        assert current_object is not None
        return current_object.start_line


class MicropythonRow(CommonRow):
    language = "mpy"

    def __init__(self, source_def_cache: SourceDefinitionCache | None = None) -> None:
        super().__init__(source_def_cache)

    def _is_data(self, row: DataRow) -> bool:
        # "const_table_data" holds info about function arguments, variables etc.,
        # so just accounting for the "real" hardcoded data
        return row.symbol_name.startswith("const_obj_")

    def _get_module_and_function(self, symbol_name: str) -> tuple[str, str]:
        for prefix in MPY_PREFIXES:
            if symbol_name.startswith(prefix):
                symbol_name = symbol_name[len(prefix) :]

        # There are possible numbers at the end, delete them, unless it really is there
        exceptions = [
            "blake_hash_writer_32",
            "_migrate_from_version_01",
            "sha256d_32",
            "groestl512d_32",
            "blake256d_32",
            "keccak_32",
            "ripemd160_32",
        ]
        if not any(symbol_name.endswith(ex) for ex in exceptions):
            symbol_name = re.sub(r"_\d+$", "", symbol_name)

        module_end = "__lt_module_gt_"
        if symbol_name.endswith(module_end):
            # It is only module name, no function
            module_path = symbol_name[: -len(module_end)]
            module_name, module_is_valid = resolve_module(module_path)
            func_name = ""
        else:
            # Iterating from back to front, trying to resolve the valid module name
            split_symbol = symbol_name.split("_")
            for i in range(len(split_symbol), 0, -1):
                module_part = "_".join(split_symbol[:i])
                func_part = "_".join(split_symbol[i:])
                module_name, module_is_valid = resolve_module(module_part)
                func_name = resolve_function_name(func_part, module_name)
                if module_is_valid:
                    break
            else:
                module_is_valid = False
                module_name = "_".join(split_symbol[:-1])
                func_name = split_symbol[-1]

        if not module_is_valid:
            module_name = f"{INVALID_FILE_PREFIX}{module_name}"

        return module_name, func_name

    def _get_definition(self, row: DataRow) -> str:
        # There is only a module, no need to locate any function definition
        if not row.func_name:
            return row.module_name

        module_defs = get_module_object_definitions(row.module_name)
        line_num = module_defs.get_line_number(row.func_name)
        return f"{row.module_name}:{line_num}" if line_num else ""


def resolve_function_name(func_name: str, module_name: str) -> str:
    # Deleting strange things at the end
    func_name = remove_strange_suffixes(func_name)

    if not func_name:
        return ""

    module_defs = get_module_object_definitions(module_name)
    return module_defs.resolve_symbol(func_name)


def remove_strange_suffixes(symbol_name: str) -> str:
    return re.sub(r"(_)?_lt_\w+_gt(_\d*)?", "", symbol_name)


@lru_cache(maxsize=None)
def get_module_object_definitions(
    module_path: str | Path,
) -> ObjectDefinition:
    """Get all the functions and classes defined in a given module"""

    def _resolve_object(
        main_node: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
        file_name: str | None = None,
    ) -> ObjectDefinition:
        """Recursively resolve object definitions from the AST"""
        functions = [
            _resolve_object(node)
            for node in main_node.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        classes = [
            _resolve_object(node)
            for node in main_node.body
            if isinstance(node, ast.ClassDef)
        ]

        return ObjectDefinition(
            name=str(file_name)
            if file_name
            else str(
                main_node.name if not isinstance(main_node, ast.Module) else "file_name"
            ),
            functions=functions,
            classes=classes,
            start_line=0 if isinstance(main_node, ast.Module) else main_node.lineno,
            end_line=main_node.body[-1].end_lineno or 999,
        )

    def _default_object() -> ObjectDefinition:
        return ObjectDefinition(
            name=str(module_path),
            functions=[],
            classes=[],
            start_line=0,
            end_line=999,
        )

    if not Path(settings.ROOT_DIR / module_path).is_file():
        return _default_object()

    with open(settings.ROOT_DIR / module_path) as file:
        # Protecting against a possible file corruption
        try:
            parsed_ast = ast.parse(file.read())
        except FileNotFoundError:
            return _default_object()

    return _resolve_object(parsed_ast, file_name=str(module_path))


@lru_cache(maxsize=None)
def resolve_module(module_name: str) -> tuple[str, bool]:
    """Completing module and making a file-path structure"""
    module_name_py = f"{module_name}.py"

    # __init__.py is a special case
    if module_name_py.endswith("__init__.py"):
        module_parts = module_name_py[: -len("__init__.py")].split("_") + [
            "__init__.py"
        ]
    else:
        module_parts = module_name_py.split("_")

    # Gradually filling the filename (generally replacing "_" with "/")
    # As some modules can themselves contain "_", we need to check if they exist
    file_path = "src"
    for part in module_parts:
        if not part:
            continue

        if file_path.endswith("_"):
            possible_path = Path(f"{file_path}{part}")
        else:
            possible_path = Path(f"{file_path}/{part}")

        if (settings.ROOT_DIR / possible_path).exists():
            file_path = str(possible_path)
        else:
            file_path = f"{possible_path}_"

    file_path = file_path.rstrip("_")

    # Special case for src/apps/monero/xmr, where both "serialize" and "serialize_message"
    # are both valid directories
    if (
        not Path(settings.ROOT_DIR / file_path).exists()
        and "apps/monero/" in file_path
        and "serialize/messages" in file_path
    ):
        file_path = file_path.replace("serialize/messages_", "serialize_messages/")

    # It may happen that the file does not exist - it may not even be a python file
    is_valid = Path(settings.ROOT_DIR / file_path).exists()

    return file_path, is_valid
