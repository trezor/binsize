from __future__ import annotations

import json
import tempfile
from pathlib import Path

from binsize import settings
from binsize.lib.source_definition_cache import SourceDefinitionCache

HERE = Path(__file__).resolve().parent


def test_is_in():
    CACHE = SourceDefinitionCache()
    assert CACHE.get("nist256p1") is None
    CACHE.add("nist256p1", "vendor/trezor-crypto/nist256p1.c:26")
    assert CACHE.get("nist256p1") == "vendor/trezor-crypto/nist256p1.c:26"
    CACHE.add("nist256p1", "vendor/trezor-crypto/nist256p1.c:2222222")
    assert CACHE.get("nist256p1") == "vendor/trezor-crypto/nist256p1.c:2222222"


def test_get_file_hash():
    CACHE = SourceDefinitionCache()
    assert (
        CACHE._get_file_hash(settings.ROOT_DIR / "vendor/trezor-crypto/nist256p1.c")
        == "829a11e46fec13e5be5d787ce0c61e4a"
    )
    assert (
        CACHE._get_file_hash(settings.ROOT_DIR / "vendor/trezor-crypto/secp256k1.c")
        == "9d5dd1ec78d886bbd972ff023c8b4b84"
    )


def test_hash_from_definition():
    CACHE = SourceDefinitionCache()
    CACHE.add("nist256p1", "vendor/trezor-crypto/nist256p1.c:26")
    assert (
        CACHE._hash_from_definition("vendor/trezor-crypto/nist256p1.c:26")
        == "829a11e46fec13e5be5d787ce0c61e4a"
    )


def test_include_hash_path():
    CACHE = SourceDefinitionCache()
    CACHE.add("nist256p1", "vendor/trezor-crypto/nist256p1.c:26")
    assert (
        CACHE.symbol_definitions["nist256p1"]["file_hash"]
        == "829a11e46fec13e5be5d787ce0c61e4a"
    )


def test_empty():
    CACHE = SourceDefinitionCache()
    assert CACHE.get("empty") is None
    CACHE.add("empty", "")
    assert CACHE.get("empty") == ""


def test_get_file_location_from_definition():
    CACHE = SourceDefinitionCache()
    assert CACHE._get_file_location_from_definition(
        "vendor/trezor-crypto/nist256p1.c:26"
    ) == str(settings.ROOT_DIR / "vendor/trezor-crypto/nist256p1.c")
    assert CACHE._get_file_location_from_definition(
        "vendor/trezor-crypto/nist256p1.c"
    ) == str(settings.ROOT_DIR / "vendor/trezor-crypto/nist256p1.c")
    assert CACHE._get_file_location_from_definition(
        "embed/extmod/modtrezorui/loader_R.h:3"
    ) == str(settings.ROOT_DIR / "embed/extmod/modtrezorui/loader_R.h")


def test_is_invalidated():
    CACHE = SourceDefinitionCache()
    CACHE.add("nist256p1", "vendor/trezor-crypto/nist256p1.c:26")
    assert CACHE.get("nist256p1") == "vendor/trezor-crypto/nist256p1.c:26"
    assert CACHE.is_invalidated("nist256p1") is False
    assert CACHE.is_invalidated("secp256k1") is False
    CACHE.symbol_definitions["nist256p1"]["file_hash"] = "123"
    assert CACHE.is_invalidated("nist256p1") is True
    assert CACHE.is_invalidated("secp256k1") is False
    CACHE.add("empty", "")
    assert CACHE.is_invalidated("empty") is False


def test_load_cache_from_file():
    with tempfile.NamedTemporaryFile("w+", suffix=".json", dir=HERE) as tmp:
        content = {
            "nist256p1": {
                "definition": "vendor/trezor-crypto/nist256p1.c:26",
                "file_hash": "829a11e46fec13e5be5d787ce0c61e4a",
            },
            "secp256k1": {
                "definition": "vendor/trezor-crypto/secp256k1.c:26",
                "file_hash": "file_hash",
            },
        }
        json.dump(content, tmp, indent=4)
        tmp.flush()

        CACHE = SourceDefinitionCache(cache_file_path=tmp.name)
        assert len(CACHE.symbol_definitions) == 2
        assert CACHE.get("nist256p1") == "vendor/trezor-crypto/nist256p1.c:26"

        # TODO: the JSON file is not deleted after test


def test_save_cache_to_file():
    with tempfile.NamedTemporaryFile("w+", suffix=".json", dir=HERE) as tmp:
        CACHE = SourceDefinitionCache(cache_file_path=tmp.name)
        CACHE.add("nist256p1", "vendor/trezor-crypto/nist256p1.c:26")
        CACHE.add("secp256k1", "vendor/trezor-crypto/secp256k1.c:26")

        CACHE._save_cache_to_file()
        tmp.flush()

        content = json.load(tmp)
        assert len(content) == 2
        assert (
            content["nist256p1"]["definition"] == "vendor/trezor-crypto/nist256p1.c:26"
        )

        # TODO: the JSON file is not deleted after test
