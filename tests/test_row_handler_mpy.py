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
    assert mod.end_line == 61
    assert mod.classes == []
    assert len(mod.functions) == 2
    assert mod.has_top_level_func("sign_tx")
    sign_tx = mod.get_func("sign_tx")
    assert sign_tx is not None
    assert sign_tx.start_line == 21
    assert sign_tx.end_line == 56
    assert mod.has_top_level_func("generate_content_signature")
    generate_content_signature = mod.get_func("generate_content_signature")
    assert generate_content_signature is not None
    assert generate_content_signature.start_line == 59
    assert generate_content_signature.end_line == 61
    assert not mod.has_top_level_func("unexisting")
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

    # Nested classes
    mod = get_module_object_definitions("src/trezor/ui/components/tt/info.py")
    first = mod.get_class("DefaultInfoConfirm")
    assert first is not None
    second = first.get_class("button")
    assert second is not None
    third = second.get_class("disabled")
    assert third is not None

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
        mod.resolve_symbol("BulletProofBuilder__prove_phase1")
        == "BulletProofBuilder._prove_phase1()"
    )


def test_module_object_definitions_line_number():
    # Getting line number
    mod = get_module_object_definitions("src/trezor/loop.py")
    assert mod.get_line_number("chan._schedule_take()") == 450
    mod = get_module_object_definitions("src/storage/cache.py")
    assert mod.get_line_number("stored_async()") == 287
    mod = get_module_object_definitions("src/apps/monero/xmr/bulletproof.py")
    assert mod.get_line_number("BulletProofBuilder._prove_phase1()") == 1787

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
            "produce_transfer_json_make_input_output",
            "src/apps/binance/helpers.py",
            "produce_transfer_json()",
        ),
        (
            "chan_put",
            "src/trezor/loop.py",
            "chan.put()",
        ),
        (
            "ButtonMono_disabled",
            "src/trezor/ui/components/tt/button.py",
            "ButtonMono.disabled",
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
            "trezor_ui_layouts_tt___init__",
            "src/trezor/ui/layouts/tt/__init__.py",
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
            "fun_data_apps_ethereum_sign_typed_data__lt_module_gt__validate_field_type",
            "src/apps/ethereum/sign_typed_data.py",
            "validate_field_type()",
        ),
        (
            "const_obj_storage_common__lt_module_gt_",
            "src/storage/common.py",
            "",
        ),
        (
            "const_obj_storage_common__lt_module_gt__0",
            "src/storage/common.py",
            "",
        ),
        (
            "const_obj_storage_common__lt_module_gt__25",
            "src/storage/common.py",
            "",
        ),
        (
            "const_table_data_apps_base__lt_module_gt__handle_Initialize",
            "src/apps/base.py",
            "handle_Initialize()",
        ),
        (
            "raw_code_apps_base__lt_module_gt__get_features",
            "src/apps/base.py",
            "get_features()",
        ),
        (
            "raw_code_apps_unexisting_base__lt_module_gt__get_features",
            "--invalid_file--src/apps/unexisting_base.py",
            "get_features",
        ),
        (
            "fun_data_apps_monero_xmr_bulletproof__lt_module_gt__BulletProofBuilder__prove_phase1",
            "src/apps/monero/xmr/bulletproof.py",
            "BulletProofBuilder._prove_phase1()",
        ),
        (
            "const_table_data_apps_bitcoin_sign_tx_approvers__lt_module_gt__Approver_finish_payment_request",
            "src/apps/bitcoin/sign_tx/approvers.py",
            "Approver.finish_payment_request()",
        ),
        (
            "const_table_data_apps_bitcoin_sign_tx_approvers__lt_module_gt__BasicApprover_approve_orig_txids__lt_genexpr_gt_",
            "src/apps/bitcoin/sign_tx/approvers.py",
            "BasicApprover.approve_orig_txids()",
        ),
        (
            "const_table_data_apps_bitcoin_keychain__lt_module_gt__get_schemas_for_coin__lt_listcomp_gt_2",
            "src/apps/bitcoin/keychain.py",
            "get_schemas_for_coin()",
        ),
        (
            "const_table_data_trezor_crypto_base32__lt_module_gt___lt_dictcomp_gt_",
            "src/trezor/crypto/base32.py",
            "",
        ),
        (
            "fun_data_storage_cache__lt_module_gt__stored_async_decorator_wrapper",
            "src/storage/cache.py",
            "stored_async()",
        ),
        (
            "fun_data_trezor_crypto_base58__lt_module_gt__blake256d_32",
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
            symbol_name="const_table_data_apps_bitcoin_keychain__lt_module_gt__get_schemas_for_coin__lt_listcomp_gt_2"
        )
    )
    assert new_row.language == "mpy"
    assert new_row.module_name == "src/apps/bitcoin/keychain.py"
    assert new_row.func_name == "get_schemas_for_coin()"


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
            "cbor_make_credential_process()",
            "src/apps/webauthn/fido2.py:1450",
        ),
        (
            "src/apps/bitcoin/sign_tx/payment_request.py",
            "PaymentRequestVerifier",
            "src/apps/bitcoin/sign_tx/payment_request.py:24",
        ),
        (
            "src/apps/bitcoin/sign_tx/payment_request.py",
            "PaymentRequestVerifier.__init__()",
            "src/apps/bitcoin/sign_tx/payment_request.py:31",
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
