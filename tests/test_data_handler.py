import pytest

from binsize.lib.data_handler import CRow, MicropythonRow, RowHandlerFactory, RustRow

from .common import mock_data_row


@pytest.mark.parametrize(
    "symbol_name",
    [
        "trezor_lib::protobuf::decode::Decoder::decode_field::hab425281b2042fd5",
        "trezor_lib::protobuf::decode::Decoder::message_from_stream",
        "compiler_builtins::math::libm::fmodf::fmodf::h71a899fe9710a6bd",
        "_$LT$T$u20$as$u20$core..convert..TryInto$LT$U$GT$$GT$::try_into::h5d525a7b159ae0d3",
        "core::result::Result$LT$T$C$E$GT$::unwrap::h4f1909c33dccc883",
    ],
)
def test_row_handler_factory_rust(symbol_name: str):
    assert isinstance(
        RowHandlerFactory()(mock_data_row(symbol_name=symbol_name)),
        RustRow,
    )


@pytest.mark.parametrize(
    "symbol_name",
    [
        "const_obj_storage_common__lt_module_gt__0",
        "fun_data_apps_workflow_handlers__lt_module_gt__find_message_handler_module",
        "const_table_data_apps_base__lt_module_gt__handle_Initialize",
        "raw_code_apps_base__lt_module_gt__get_features",
    ],
)
def test_row_handler_factory_mpy(symbol_name: str):
    assert isinstance(
        RowHandlerFactory()(mock_data_row(symbol_name=symbol_name)),
        MicropythonRow,
    )


@pytest.mark.parametrize(
    "symbol_name",
    [
        "const_crypto",
        "fun_crypto",
        "array_subscr",
        "ge25519_fromfe_frombytes_vartime",
        "two_over_pi",
    ],
)
def test_row_handler_factory_c(symbol_name: str):
    assert isinstance(
        RowHandlerFactory()(mock_data_row(symbol_name=symbol_name)),
        CRow,
    )
