import pytest

from binsize.lib.row_handler_mpy import (
    MicropythonRow,
    get_module_object_definitions,
    remove_strange_suffixes,
    resolve_function_name,
    resolve_module,
)

from .common import mock_data_row

MPR = MicropythonRow()


def test_module_object_definitions_general():
    # Just top-level functions
    mod = get_module_object_definitions("src/apps/binance/sign_tx.py")
    assert mod.start_line == 0
    assert mod.end_line == 63
    assert mod.classes == []
    assert len(mod.functions) == 1
    assert mod.has_top_level_func("sign_tx")
    sign_tx = mod.get_func("sign_tx")
    assert sign_tx is not None
    assert sign_tx.start_line == 11
    assert sign_tx.end_line == 63
    unexisting = mod.get_func("unexisting")
    assert unexisting is None

    # Top-level classes with functions inside
    mod = get_module_object_definitions("src/trezor/crypto/scripts.py")
    assert mod.functions == []
    assert len(mod.classes) == 2
    assert mod.has_top_level_class("sha256_ripemd160")
    sha256_ripemd160 = mod.get_class("sha256_ripemd160")
    assert sha256_ripemd160 is not None
    assert sha256_ripemd160.has_top_level_func("digest")
    blake256_ripemd160 = mod.get_class("blake256_ripemd160")
    assert blake256_ripemd160 is not None
    assert blake256_ripemd160.has_top_level_func("digest")
    assert not mod.has_top_level_class("unexisting")
    unexisting = mod.get_class("unexisting")
    assert unexisting is None

    # Both top-level functions and top-level classes with functions inside
    mod = get_module_object_definitions("src/trezor/loop.py")
    assert mod.has_top_level_func("schedule")
    assert mod.has_top_level_func("_step")
    assert mod.has_top_level_class("sleep")
    sleep_class = mod.get_class("sleep")
    assert sleep_class is not None
    assert sleep_class.has_top_level_func("handle")
    assert mod.has_top_level_class("race")
    race_class = mod.get_class("race")
    assert race_class is not None
    assert race_class.has_top_level_func("_finish")

    # Nested functions
    mod = get_module_object_definitions("src/storage/cache.py")
    assert mod.has_top_level_func("stored_async")
    stored_async = mod.get_func("stored_async")
    assert stored_async is not None
    stored_async_decorator = stored_async.get_func("decorator")
    assert stored_async_decorator is not None
    stored_async_decorator_wrapper = stored_async_decorator.get_func("wrapper")
    assert stored_async_decorator_wrapper is not None


def test_module_object_definitions_symbol_resolution():
    # Symbol resolution functions in functions
    mod = get_module_object_definitions("src/storage/cache.py")
    assert mod.resolve_symbol("acaca_badaca") == ""
    assert mod.resolve_symbol("stored_async") == "stored_async()"
    assert mod.resolve_symbol("stored_async_decorator") == "stored_async()"
    assert mod.resolve_symbol("stored_async_decorator_wrapper") == "stored_async()"

    # Symbol resolution functions in classes
    mod = get_module_object_definitions("src/apps/monero/xmr/bulletproof.py")
    assert (
        mod.resolve_symbol("BulletProofPlusBuilder__gprec_aux")
        == "BulletProofPlusBuilder._gprec_aux()"
    )


def test_module_object_definitions_line_number():
    # Getting line number
    mod = get_module_object_definitions("src/trezor/loop.py")
    assert mod.get_line_number("chan._schedule_take()") == 428
    mod = get_module_object_definitions("src/storage/cache.py")
    assert mod.get_line_number("stored_async()") == 329
    mod = get_module_object_definitions("src/apps/monero/xmr/bulletproof.py")
    assert mod.get_line_number("KeyVPrecomp.to()") == 662

    # Unexisting function
    mod = get_module_object_definitions("src/apps/monero/xmr/bulletproof.py")
    assert mod.get_line_number("unexisting()") == 0

    # Unexisting module
    mod = get_module_object_definitions("src/apps/monero/xmr/unexisting.py")
    assert mod.get_line_number("unexisting()") == 0


@pytest.mark.parametrize(
    "symbol_part,module,func",
    [
        (
            "BasicApprover_approve_orig_txids__lt_genexpr_gt_",
            "src/apps/bitcoin/sign_tx/approvers.py",
            "BasicApprover.approve_orig_txids()",
        ),
        ("PathSchema", "src/apps/common/paths.py", "PathSchema"),
        ("PathSchema___init__", "src/apps/common/paths.py", "PathSchema.__init__()"),
        (
            "with_keychain_from_path",
            "src/apps/ethereum/keychain.py",
            "with_keychain_from_path()",
        ),
        (
            "with_keychain_from_path_decorator",
            "src/apps/ethereum/keychain.py",
            "with_keychain_from_path()",
        ),
        (
            "with_keychain_from_path_decorator_wrapper",
            "src/apps/ethereum/keychain.py",
            "with_keychain_from_path()",
        ),
        (
            "blake256_ripemd160_digest",
            "src/trezor/crypto/scripts.py",
            "blake256_ripemd160.digest()",
        ),
        (
            "BulletProofPlusBuilder__prove_batch_main_aR1_fnc",
            "src/apps/monero/xmr/bulletproof.py",
            "BulletProofPlusBuilder._prove_batch_main()",
        ),
        (
            "require_confirm_transfer_make_input_output_pages",
            "src/apps/binance/layout.py",
            "require_confirm_transfer()",
        ),
        (
            "chan_put",
            "src/trezor/loop.py",
            "chan.put()",
        ),
        ("__lt_dictcomp_gt_", "src/storage/device.py", ""),
    ],
)
def test_resolve_function_name(symbol_part: str, module: str, func: str):
    assert resolve_function_name(symbol_part, module) == func


@pytest.mark.parametrize(
    "input,output",
    [
        (
            "BasicApprover_approve_orig_txids__lt_genexpr_gt_",
            "BasicApprover_approve_orig_txids",
        ),
        ("PathSchema__copy_container__lt_listcomp_gt_2", "PathSchema__copy_container"),
    ],
)
def test_remove_strange_suffixes(input: str, output: str):
    assert remove_strange_suffixes(input) == output


@pytest.mark.parametrize(
    "symbol,module,is_valid",
    [
        (
            "apps_bitcoin_sign_tx_matchcheck",
            "src/apps/bitcoin/sign_tx/matchcheck.py",
            True,
        ),
        (
            "apps_cardano_helpers_hash_builder_collection",
            "src/apps/cardano/helpers/hash_builder_collection.py",
            True,
        ),
        (
            "apps_monero_xmr_serialize_messages_tx_ct_key",
            "src/apps/monero/xmr/serialize_messages/tx_ct_key.py",
            True,
        ),
        (
            "apps_monero_xmr_serialize_base_types",
            "src/apps/monero/xmr/serialize/base_types.py",
            True,
        ),
        (
            "trezor_ui_layouts_tt_v2___init__",
            "src/trezor/ui/layouts/tt_v2/__init__.py",
            True,
        ),
        (
            "apps_monero_signing___init__",
            "src/apps/monero/signing/__init__.py",
            True,
        ),
        (
            "apps_bitcoin_sign_tx_matchcheck_unexisting",
            "src/apps/bitcoin/sign_tx/matchcheck_unexisting.py",
            False,
        ),
    ],
)
def test_resolve_module(symbol: str, module: str, is_valid: bool):
    assert resolve_module(symbol) == (module, is_valid)


@pytest.mark.parametrize(
    "symbol,module,func",
    [
        (
            "fun_data_apps_ethereum_sign_typed_data__lt_module_gt_",
            "src/apps/ethereum/sign_typed_data.py",
            "",
        ),
        (
            "children_apps_eos_sign_tx__lt_module_gt_",
            "src/apps/eos/sign_tx.py",
            "",
        ),
        (
            "raw_code_apps_ethereum_sign_typed_data_validate_field_type",
            "src/apps/ethereum/sign_typed_data.py",
            "validate_field_type()",
        ),
        (
            "fun_data_apps_ethereum_sign_typed_data_validate_field_type",
            "src/apps/ethereum/sign_typed_data.py",
            "validate_field_type()",
        ),
        (
            "const_obj_storage_common",
            "src/storage/common.py",
            "",
        ),
        (
            "const_obj_storage_common_0",
            "src/storage/common.py",
            "",
        ),
        (
            "const_obj_storage_common_25",
            "src/storage/common.py",
            "",
        ),
        (
            "const_obj_apps_monero_xmr_serialize_messages_tx_rsig_bulletproof_0",
            "src/apps/monero/xmr/serialize_messages/tx_rsig_bulletproof.py",
            "",
        ),
        (
            "fun_data_apps_base_handle_Initialize",
            "src/apps/base.py",
            "handle_Initialize()",
        ),
        (
            "raw_code_apps_base_get_features",
            "src/apps/base.py",
            "get_features()",
        ),
        (
            "raw_code_apps_unexisting_base_get_features",
            "--invalid_file--apps_unexisting_base_get",
            "features",
        ),
        (
            "fun_data_apps_monero_xmr_bulletproof_BulletProofPlusBuilder__gprec_aux",
            "src/apps/monero/xmr/bulletproof.py",
            "BulletProofPlusBuilder._gprec_aux()",
        ),
        (
            "const_qstr_table_data_apps_cardano_layout",
            "src/apps/cardano/layout.py",
            "",
        ),
        (
            "const_obj_table_data_apps_cardano_layout",
            "src/apps/cardano/layout.py",
            "",
        ),
        (
            "const_qstr_table_data_trezor_ui_layouts_tt_v2___init__",
            "src/trezor/ui/layouts/tt_v2/__init__.py",
            "",
        ),
        (
            "fun_data_storage_cache_stored_async_decorator_wrapper",
            "src/storage/cache.py",
            "stored_async()",
        ),
        (
            "fun_data_trezor_crypto_base58_blake256d_32",
            "src/trezor/crypto/base58.py",
            "blake256d_32()",
        ),
    ],
)
def test_get_module_and_function(symbol: str, module: str, func: str):
    assert MPR._get_module_and_function(symbol) == (module, func)


def test_add_basic_info_row_handlers():
    new_row = MPR.add_basic_info(
        mock_data_row(
            symbol_name="fun_data_apps_bitcoin_keychain__get_schemas_for_coin__lt_listcomp_gt_"
        )
    )
    assert new_row.language == "mpy"
    assert new_row.module_name == "src/apps/bitcoin/keychain.py"
    assert new_row.func_name == "_get_schemas_for_coin()"


@pytest.mark.parametrize(
    "module,func,definition",
    [
        (
            "src/apps/webauthn/fido2.py",
            "",
            "src/apps/webauthn/fido2.py",
        ),
        (
            "src/apps/webauthn/fido2.py",
            "_cbor_make_credential_process()",
            "src/apps/webauthn/fido2.py:1484",
        ),
        (
            "src/apps/bitcoin/sign_tx/payment_request.py",
            "PaymentRequestVerifier",
            "src/apps/bitcoin/sign_tx/payment_request.py:18",
        ),
        (
            "src/apps/bitcoin/sign_tx/payment_request.py",
            "PaymentRequestVerifier.__init__()",
            "src/apps/bitcoin/sign_tx/payment_request.py:25",
        ),
        (
            "src/apps/bitcoin/sign_tx/payment_request.py",
            "unexisting()",
            "",
        ),
        (
            "src/apps/bitcoin/sign_tx/unexisting.py",
            "PaymentRequestVerifier.__init__()",
            "",
        ),
    ],
)
def test_get_definition(module: str, func: str, definition: str):
    assert (
        MPR._get_definition(mock_data_row(module_name=module, func_name=func))
        == definition
    )
