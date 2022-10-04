"""
Read-only access to settings.

Settings file is editable by user.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from .user_data import config_dir

# TODO: consider adding project-specific sections to settings

HERE = Path(__file__).parent

TEMPLATE = HERE / "settings_template.json"
SETTINGS = config_dir / "settings.json"

# Copying the template content into a user directory,
# where it can be edited
if not SETTINGS.exists():
    SETTINGS.write_text(TEMPLATE.read_text())

print(f"Settings file: {SETTINGS}")

if TYPE_CHECKING:
    KEYS = Literal["root", "elf_file", "map_file", "build_cmd"]


def get_settings() -> dict[str, str]:
    """Get the settings as a dict."""
    with open(SETTINGS) as f:
        return json.load(f)


def update_settings(key: str, value: str) -> None:
    """Update a value in the settings file."""
    settings = get_settings()
    settings[key] = value
    with open(SETTINGS, "w") as f:
        json.dump(settings, f, indent=4)


def set_root_dir(root_dir: str) -> None:
    """Set a new root directory if it differs from the current one."""
    current_root_dir = get("root")
    if current_root_dir != root_dir:
        print(f"Setting root dir to {root_dir}")
        update_settings("root", root_dir)


def get(key: KEYS) -> str:
    """Get a value from the settings file."""
    return resolve_variables(get_settings()[key])


def resolve_variables(value: str) -> str:
    """Allows for using variables in JSON file.

    Variables are enclosed in double curly braces, e.g.:
    `{{root}}/build` will resolve the `root` variable/key
    from the JSON file.
    """

    def _replace_by_variable(m: re.Match[str]) -> str:
        variable = m.group(1).strip()
        return get(variable)  # type: ignore

    return re.sub(r"\{\{(.*?)\}\}", _replace_by_variable, value)


# Checking env variable containing the root dir
# and writing it into file if exists
env_root_dir = os.getenv("BINSIZE_ROOT_DIR")
if env_root_dir is not None:
    set_root_dir(env_root_dir)


# Caching frequently accessed paths
ROOT_DIR = Path(get("root"))
ELF_FILE = Path(get("elf_file"))
MAP_FILE = Path(get("map_file"))
