"""
Outputting a symbol tree from a map file.
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from typing_extensions import TypeAlias

from .. import settings

if TYPE_CHECKING:
    SectionItemTree: TypeAlias = "dict[str, SectionItem | SectionItemTree]"

REPLACEMENTS = {
    "$LT$": "<",
    "$GT$": ">",
    "$u20$": " ",
    "$RF$": "&",
    "..": "::",
}


@dataclass
class SectionItem:
    name: str
    entries: list[Entry] = field(default_factory=list)

    def total_size(self) -> int:
        return sum(e.size for e in self.entries)


@dataclass
class Entry:
    section: SectionItem
    address: int
    size: int
    comment: str


def show_map_file_tree(
    map_file: str | Path,
    section_to_get: str,
    file_to_save: str | Path | None = None,
) -> None:
    section_data = get_section_data(map_file, section_to_get)

    section_tree = _build_per_char_tree(section_data)
    section_tree = _prune_subtree(section_tree)

    output = _subtree_sizes_output(section_tree)

    if file_to_save:
        print(f"Saving output to {file_to_save}")
        with open(file_to_save, "w") as f:
            f.write(output)
    else:
        print(output)


def get_section_data(file: str | Path, section_to_get: str) -> dict[str, SectionItem]:
    with open(file, "r") as f:
        lines = f.read().splitlines()

    # throw away lines until we encounter our section
    while not (line := lines.pop(0)).startswith(f"{section_to_get} "):
        pass

    section_data: dict[str, SectionItem] = {}
    current_section: SectionItem | None = None
    for line in lines:
        if line.startswith("."):  # another section starting
            break
        elems = line.split()
        if elems and not elems[0].startswith("0x"):
            name = _rust_demangle(elems[0])
            current_section = section_data.setdefault(name, SectionItem(name))
            elems.pop(0)
        if elems:
            assert current_section is not None
            address = int(elems[0], 16)
            if len(elems) > 1 and elems[1].startswith("0x"):
                size = int(elems[1], 16)
                comment = " ".join(elems[2:])
            else:
                size = 0
                comment = " ".join(elems[1:])
            current_section.entries.append(
                Entry(
                    section=current_section,
                    address=address,
                    size=size,
                    comment=comment,
                )
            )

    return section_data


def _rust_demangle(symbol: str) -> str:
    for k, v in REPLACEMENTS.items():
        symbol = symbol.replace(k, v)
    return symbol


def _build_per_char_tree(section_data: dict[str, SectionItem]) -> SectionItemTree:
    section_tree: SectionItemTree = {}
    # build per-char tree
    for name, section in section_data.items():
        current_subtree = section_tree
        for char in name:
            current_subtree = current_subtree.setdefault(char, {})
            assert isinstance(current_subtree, dict)
        current_subtree[""] = section

    return section_tree


# prune tree so that no single-entry subtree exists
def _prune_subtree(tree: SectionItemTree) -> SectionItemTree:
    new_tree: SectionItemTree = {}
    for entry, subtree in tree.items():
        while isinstance(subtree, dict) and len(subtree) == 1:
            k, subtree = subtree.popitem()
            entry += k
        if isinstance(subtree, dict):
            subtree = _prune_subtree(subtree)
        new_tree[entry] = subtree
    return new_tree


def _total_subtree_size(tree: SectionItemTree) -> int:
    total = 0
    for subtree in tree.values():
        if isinstance(subtree, dict):
            total += _total_subtree_size(subtree)
        else:
            total += subtree.total_size()
    return total


def _subtree_sizes_output(tree: SectionItemTree, name_prefix: str = "") -> str:
    lines: list[str] = []
    for name, subtree in tree.items():
        if isinstance(subtree, dict):
            subtree_name = name_prefix + name
            size = _total_subtree_size(subtree)
            lines.append(f"{subtree_name}: {size}")
            if size > 0:
                subsizes = _subtree_sizes_output(subtree, subtree_name)
                lines.append(textwrap.indent(subsizes, "    "))
        else:
            lines.append(f"*{subtree.name}: {subtree.total_size()}")
    return "\n".join(lines)


if __name__ == "__main__":
    show_map_file_tree(settings.MAP_FILE, ".flash")
