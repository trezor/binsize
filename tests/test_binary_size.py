import tempfile
from pathlib import Path

import pytest

from binsize import settings
from binsize.lib.api import DataRow

from .common import BLOATY_MOCK_CSV, get_bloaty_BS, mock_data_row

HERE = Path(__file__).resolve().parent


def test_load_file():
    unexisting_file = Path("unexisting.elf")
    assert not unexisting_file.exists()
    BS = get_bloaty_BS()
    with pytest.raises(FileNotFoundError):
        BS.load_file(unexisting_file)

    if not settings.ELF_FILE.exists():
        pytest.fail(f"{settings.ELF_FILE} not found")
    BS = get_bloaty_BS()
    BS.load_file(settings.ELF_FILE)
    assert BS.get_len() > 0


def test_load_csv():
    BS = get_bloaty_BS().load_csv(BLOATY_MOCK_CSV)
    assert BS.get_len() == 7
    BS = get_bloaty_BS().load_csv(BLOATY_MOCK_CSV, sections=(".flash",))
    assert BS.get_len() == 3


def test_add_basic_info():
    BS = get_bloaty_BS().load_csv(BLOATY_MOCK_CSV)
    assert BS.get()[0].language == ""
    assert BS.get()[1].func_name == ""
    assert BS.get()[6].module_name == ""
    BS.add_basic_info()
    assert BS.get()[0].language == "C"
    assert BS.get()[1].func_name == "token_by_chain_address()"
    assert BS.get()[6].module_name == "embed/rust/src/protobuf/decode.rs"


def test_add_definitions():
    BS = get_bloaty_BS().load_csv(BLOATY_MOCK_CSV)
    assert BS.get()[0].language == ""
    assert BS.get()[1].func_name == ""
    assert BS.get()[6].module_name == ""
    assert not any(bool(row.source_definition) for row in BS.get())

    # Targeting only one
    BS.add_definitions(condition=lambda row: "protobuf" in row.symbol_name)
    assert len([row for row in BS.get() if bool(row.source_definition)]) == 1

    # All others as well
    BS.add_definitions()
    assert len([row for row in BS.get() if bool(row.source_definition)]) > 1


def test_show_file():
    BS = get_bloaty_BS().load_csv(BLOATY_MOCK_CSV)
    with tempfile.NamedTemporaryFile("w+", suffix=".txt", dir=HERE) as tmp:
        BS.show(tmp.name)
        content = tmp.readlines()
        assert len(content) == 8
        assert "SUMMARY" in content[0]


def test_show_terminal(capfd):
    BS = get_bloaty_BS().load_csv(BLOATY_MOCK_CSV)
    BS.show()
    captured = capfd.readouterr()
    content = captured.out.splitlines()
    assert len(content) == 8
    assert "SUMMARY" in content[-1]


def test_get_size_and_len():
    rows = 3 * [
        mock_data_row(size=60, logic_size=60),
        mock_data_row(size=16, data_size=16),
        mock_data_row(size=328, logic_size=328),
    ]
    BS = get_bloaty_BS().load_data(rows)
    assert BS.get() == rows
    assert BS.get_size() == 3 * (60 + 16 + 328)
    assert BS.get_len() == 3 * 3
    assert BS._get_logic_size() == 3 * (60 + 328)
    assert BS._get_data_size() == 3 * (16)


def test_get_summary_data():
    rows = [
        mock_data_row(size=60, logic_size=60),
        mock_data_row(size=16, data_size=16),
        mock_data_row(size=328, logic_size=328),
    ]
    BS = get_bloaty_BS().load_data(rows)
    assert BS._get_data_summary() == "SUMMARY: 3 rows, 404 bytes in total (L388 D16)."


def test_aggregate():
    rows = [
        mock_data_row(
            module_name="src/apps/management/change_pin.py",
            func_name="change_pin()",
            size=191,
            logic_size=191,
        ),
        mock_data_row(
            module_name="src/apps/management/change_pin.py",
            func_name="change_pin()",
            size=60,
            logic_size=60,
        ),
        mock_data_row(
            module_name="src/apps/management/change_pin.py",
            func_name="change_pin()",
            size=16,
            data_size=16,
        ),
        mock_data_row(
            module_name="src/apps/management/change_pin.py",
            func_name="change_pin()",
            size=16,
            data_size=16,
        ),
        mock_data_row(
            module_name="src/apps/management/change_pin.py",
            func_name="change_pin()",
            size=12,
            data_size=12,
        ),
        mock_data_row(
            module_name="src/apps/management/recovery_device/homescreen.py",
            func_name="_finish_recovery()",
            size=12,
            logic_size=12,
        ),
        mock_data_row(
            module_name="src/apps/management/recovery_device/homescreen.py",
            func_name="_finish_recovery()",
            size=16,
            data_size=16,
        ),
        mock_data_row(
            module_name="src/apps/management/change_wipe_code.py",
            func_name="_wipe_code_mismatch()",
            size=32,
            logic_size=32,
        ),
    ]

    expected_result = [
        mock_data_row(
            module_name="src/apps/management/change_pin.py",
            func_name="change_pin()",
            size=191 + 60 + 16 + 16 + 12,
            number_of_symbols=5,
            logic_size=191 + 60,
            data_size=16 + 16 + 12,
        ),
        mock_data_row(
            module_name="src/apps/management/recovery_device/homescreen.py",
            func_name="_finish_recovery()",
            size=12 + 16,
            number_of_symbols=2,
            logic_size=12,
            data_size=16,
        ),
        mock_data_row(
            module_name="src/apps/management/change_wipe_code.py",
            func_name="_wipe_code_mismatch()",
            size=32,
            number_of_symbols=1,
            logic_size=32,
        ),
    ]

    BS = get_bloaty_BS()
    assert BS.load_data(rows).aggregate().get() == expected_result

    initial_overall_size = sum(row.size for row in rows)
    deduplicated_overall_size = sum(row.size for row in expected_result)
    assert initial_overall_size == deduplicated_overall_size


def test_sort():
    # Size - int
    rows = [
        mock_data_row(size=60),
        mock_data_row(size=16),
        mock_data_row(size=328),
    ]
    BS = get_bloaty_BS().load_data(rows)
    assert BS.get() == rows
    assert BS.sort().get() == [
        mock_data_row(size=328),
        mock_data_row(size=60),
        mock_data_row(size=16),
    ]
    assert BS.sort(key=lambda row: row.size, reverse=False).get() == [
        mock_data_row(size=16),
        mock_data_row(size=60),
        mock_data_row(size=328),
    ]

    # Name - str
    rows = [
        mock_data_row(module_name="src/apps/management/change_pin.py"),
        mock_data_row(module_name="src/apps/management/recovery_device/homescreen.py"),
        mock_data_row(module_name="embed/rust/src/protobuf/decode.rs"),
        mock_data_row(module_name=""),
    ]
    BS = get_bloaty_BS().load_data(rows)
    assert BS.get() == rows
    assert BS.sort(key=lambda row: row.module_name).get() == [
        mock_data_row(module_name="src/apps/management/recovery_device/homescreen.py"),
        mock_data_row(module_name="src/apps/management/change_pin.py"),
        mock_data_row(module_name="embed/rust/src/protobuf/decode.rs"),
        mock_data_row(module_name=""),
    ]


def test_filter():
    rows = [
        mock_data_row(
            module_name="src/apps/management/change_pin.py",
            func_name="change_pin()",
            language="mpy",
            size=60,
        ),
        mock_data_row(
            module_name="src/apps/management/change_pin.py",
            func_name="change_pin()",
            language="mpy",
            size=16,
        ),
        mock_data_row(
            module_name="src/apps/management/recovery_device/homescreen.py",
            func_name="_finish_recovery()",
            language="mpy",
            size=12,
        ),
        mock_data_row(
            module_name="embed/rust/src/protobuf/decode.rs",
            func_name="Decoder::decode_defaults_into()",
            language="Rust",
            size=16,
        ),
        mock_data_row(
            module_name="",
            func_name="ed25519_sign_ext",
            language="C",
            size=328,
        ),
    ]

    BS = get_bloaty_BS().load_data(rows)
    assert BS.get() == rows

    def filter_func(row: DataRow) -> bool:
        return row.size > 20 or row.language == "Rust"

    # "Normal" function
    assert BS.filter(filter_func).get() == [
        mock_data_row(
            module_name="src/apps/management/change_pin.py",
            func_name="change_pin()",
            language="mpy",
            size=60,
        ),
        mock_data_row(
            module_name="embed/rust/src/protobuf/decode.rs",
            func_name="Decoder::decode_defaults_into()",
            language="Rust",
            size=16,
        ),
        mock_data_row(
            module_name="",
            func_name="ed25519_sign_ext",
            language="C",
            size=328,
        ),
    ]

    # Lambda function
    assert BS.filter(lambda row: row.language == "C").get() == [
        mock_data_row(
            module_name="",
            func_name="ed25519_sign_ext",
            language="C",
            size=328,
        ),
    ]
