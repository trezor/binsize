from __future__ import annotations

import atexit
import hashlib
import json
from pathlib import Path

from typing_extensions import TypedDict

from .. import settings
from .api import SourceDefinitionCacheAPI


class SourceDefinition(TypedDict):
    definition: str
    file_hash: str


class SourceDefinitionCache(SourceDefinitionCacheAPI):
    def __init__(self, cache_file_path: str | Path | None = None):
        self.cache_file_path = cache_file_path
        if self.cache_file_path is None:
            self.symbol_definitions: dict[str, SourceDefinition] = {}
        else:
            print(f"Cache file: {self.cache_file_path}")
            self.symbol_definitions = self._load_cache_from_file()
            # So that we save the cache at the end
            atexit.register(self._save_cache_to_file)

    def add(self, symbol: str, definition: str) -> None:
        # When definition is empty, we cannot calculate any file hash
        # Otherwise, storing it as a way to invalidate the definition if file changes
        if not definition:
            file_hash = ""
        else:
            file_hash = self._hash_from_definition(definition)
        self.symbol_definitions[symbol] = {
            "definition": definition,
            "file_hash": file_hash,
        }

    def get(self, symbol: str) -> str | None:
        if symbol in self.symbol_definitions:
            return self.symbol_definitions[symbol]["definition"]
        else:
            return None

    def is_invalidated(self, symbol: str) -> bool:
        """Definitions are invalidated if the file they are defined in has changed."""
        if symbol in self.symbol_definitions:
            definition = self.symbol_definitions[symbol]["definition"]
            # Empty definitions cannot be invalidated
            if not definition:
                return False
            # Checking if a file has the same hash as it was when the definition was added
            last_hash = self.symbol_definitions[symbol]["file_hash"]
            file_path = self._get_file_location_from_definition(definition)
            return self._get_file_hash(file_path) != last_hash
        else:
            return False

    def _hash_from_definition(self, definition: str) -> str:
        file_path = self._get_file_location_from_definition(definition)
        return self._get_file_hash(file_path)

    @staticmethod
    def _get_file_hash(file_path: str | Path) -> str:
        try:
            content = Path(file_path).read_bytes()
        except FileNotFoundError:
            return ""
        return hashlib.md5(content).hexdigest()

    @staticmethod
    def _get_file_location_from_definition(symbol_definition: str) -> str:
        # Delete the line number
        file_name = symbol_definition.split(":")[0]
        return str(settings.ROOT_DIR / file_name)

    def _load_cache_from_file(self) -> dict[str, SourceDefinition]:
        assert self.cache_file_path is not None
        try:
            with open(self.cache_file_path, "r") as f:
                return json.load(f)
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_cache_to_file(self) -> None:
        assert self.cache_file_path is not None
        with open(self.cache_file_path, "w") as f:
            json.dump(self.symbol_definitions, f, indent=4)
