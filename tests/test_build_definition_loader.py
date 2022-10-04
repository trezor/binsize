from __future__ import annotations

import pytest

from binsize import settings
from binsize.lib.build_definition_loader import BuildDefinitionLoader


def test_loader():
    def_loader = BuildDefinitionLoader()
    if not settings.ELF_FILE.exists():
        pytest.fail(f"{settings.ELF_FILE} not found")
    def_loader.load(settings.ELF_FILE)
    assert def_loader.get("unexisting") is None
    assert def_loader.get("nist256p1") == "vendor/trezor-crypto/nist256p1.c:26"
