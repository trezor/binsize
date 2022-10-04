"""
Creates a tree of files with overall sizes of symbols defined in them.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ..lib.api import BinarySizeAPI, DataRow

    FileTree = dict[str, "FileTree" | list["File"]]


@dataclass
class File:
    name: str
    size: int


class SizeTreePlugin:
    def __init__(
        self,
        binary_size: BinarySizeAPI,
    ):
        self.binary_size = binary_size

    def get(self) -> FileTree:
        """Get the tree."""
        recursive_path: FileTree = get_default_tree()
        data = self.binary_size.get()
        all_unique_files = {get_file(item) for item in data}
        file_sizes = get_file_sizes(data)
        for file in all_unique_files:
            size = file_sizes.get(file, 0)
            attach(file, recursive_path, size)

        return recursive_path

    def show(self) -> None:
        """Print the tree."""
        recursive_path = self.get()
        pretty_print(recursive_path)


# To identify a list of files in a dict - otherwise its keys are directory names
FILE_MARKER = "<files>"


def get_default_tree() -> FileTree:
    """Get the default tree structure."""
    return defaultdict(dict, ((FILE_MARKER, []),))


def get_file(row: DataRow) -> str:
    """Get the file name from the data row."""
    if row.module_name:
        return row.module_name
    else:
        return row.source_definition.split(":", 1)[0]


def get_file_sizes(data: list[DataRow]) -> dict[str, int]:
    """Get the size of each file."""
    file_sizes: dict[str, int] = defaultdict(int)
    for item in data:
        file = get_file(item)
        file_sizes[file] += item.size
    return file_sizes


def attach(branch: str, trunk: FileTree, file_size: int) -> None:
    """Insert a branch of directories on its trunk."""
    parts = branch.split("/", 1)
    if len(parts) == 1:  # branch is a file
        file = File(name=parts[0], size=file_size)
        trunk[FILE_MARKER].append(file)
    else:
        node, others = parts
        if node not in trunk:
            trunk[node] = get_default_tree()
        new_trunk = trunk[node]
        assert isinstance(new_trunk, dict)
        attach(others, new_trunk, file_size)


def pretty_print(d: FileTree, indent: int = 0) -> None:
    """Print the file tree structure with proper indentation and sizes."""
    space = "    "
    for key, value in sorted(d.items(), key=lambda item: item[0]):
        if key == FILE_MARKER:
            assert isinstance(value, list)
            if value:
                for file in sorted(value, key=lambda f: f.size, reverse=True):
                    print(f"{space * indent}{file.size:_} {file.name}")
        else:
            assert isinstance(value, dict)
            size = get_dir_size(value)
            print(f"{space * indent}{size:_} {key}")
            pretty_print(value, indent + 1)


def get_dir_size(d: FileTree) -> int:
    """Get the total size of all files in the directory, including sub-directories."""
    size = 0
    for key, value in d.items():
        if key == FILE_MARKER:
            assert isinstance(value, list)
            for file in value:
                size += file.size
        else:
            assert isinstance(value, dict)
            size += get_dir_size(value)
    return size
