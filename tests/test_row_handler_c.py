import pytest

from binsize.lib.row_handler_c import (
    CRow,
    clean_special_symbols,
    validate_line_for_definition,
)

from .common import mock_data_row

CR = CRow()


@pytest.mark.parametrize(
    "symbol,symbol_after",
    [
        (
            "normal",
            "normal",
        ),
        (
            "__compound_literal.53",
            "__compound_literal",
        ),
        (
            "OUTLINED_FUNCTION_15",
            "OUTLINED_FUNCTION",
        ),
        (
            "__func__.13",
            "__func__",
        ),
        (
            "pb_read.part.0",
            "pb_read",
        ),
        (
            "svc_setpriority.constprop.0",
            "svc_setpriority",
        ),
        (
            ".rodata::L__unnamed_22",
            ".rodata::L__unnamed",
        ),
    ],
)
def test_clean_special_symbols(symbol: str, symbol_after: str):
    assert clean_special_symbols(symbol) == symbol_after


@pytest.mark.parametrize(
    "build_definition,result",
    [
        (
            "vendor/secp256k1-zkp/src/precomputed_ecmult_gen.c:14",
            True,
        ),
        (
            "vendor/micropython/py/qstr.c:103",
            True,
        ),
        (
            "vendor/trezor-crypto/ed25519-donna/ed25519-donna-basepoint-table.c:4",
            True,
        ),
        (
            "vendor/trezor-crypto/blake2b.c:213",
            False,
        ),
        (
            "vendor/trezor-crypto/aes/aescrypt.c:232",
            False,
        ),
        (
            "embed/extmod/modtrezorui/qr-code-generator/qrcodegen.c:207",
            False,
        ),
        (
            "vendor/micropython/ports/powerpc/mpconfigport.h",
            False,
        ),
    ],
)
def test_is_data(build_definition: str, result: bool):
    row = mock_data_row(build_definition=build_definition)
    assert CR._is_data(row) == result


@pytest.mark.parametrize(
    "symbol,module,func",
    [
        (
            "mp_frozen_mpy_names",
            "",
            "mp_frozen_mpy_names",
        ),
        (
            "mod_trezorcrypto_from_seed_slip23",
            "",
            "mod_trezorcrypto_from_seed_slip23",
        ),
    ],
)
def test_get_module_and_function(symbol: str, module: str, func: str):
    assert CR._get_module_and_function(symbol) == (module, func)


def test_add_basic_info_row_handlers():
    new_row = CR.add_basic_info(mock_data_row(symbol_name="mp_frozen_mpy_names"))
    assert new_row.language == "C"
    assert new_row.module_name == ""
    assert new_row.func_name == "mp_frozen_mpy_names"


@pytest.mark.parametrize(
    "func,definition",
    [
        (
            "secp256k1_ecmult_gen_prec_table",
            "vendor/secp256k1-zkp/src/precomputed_ecmult_gen.c:11",
        ),
        (
            "nist256p1",
            "vendor/trezor-crypto/nist256p1.c:26",
        ),
        (
            "mod_trezorcrypto_cardano_derive_icarus",
            "embed/extmod/modtrezorcrypto/modtrezorcrypto-cardano.h:47",
        ),
        (
            "mp_qstr_const_pool",
            "vendor/micropython/py/qstr.c:93",
        ),
        (
            "ge25519_niels_base_multiples",
            "vendor/trezor-crypto/ed25519-donna/ed25519-donna-basepoint-table.c:4",
        ),
        (
            "qrcodegen_encodeSegmentsAdvanced",
            "vendor/QR-Code-generator/c/qrcodegen.c:207",
        ),
        (
            "curve25519_mul",
            "vendor/trezor-crypto/ed25519-donna/curve25519-donna-32bit.c:160",
        ),
        (
            "groestl_big_core",
            "vendor/trezor-crypto/groestl.c:689",
        ),
        (
            "groestl_big_close.constprop.0",
            "vendor/trezor-crypto/groestl.c:730",
        ),
        (
            "words_button_seq",
            "vendor/trezor-crypto/slip39_wordlist.h:44",
        ),
        (
            "mod_trezorconfig_check_pin_obj",
            "embed/extmod/modtrezorconfig/modtrezorconfig.c",
        ),
        (
            "mod_trezorio_VCP_locals_dict",
            "embed/extmod/modtrezorio/modtrezorio-vcp.h",
        ),
        (
            "mod_trezorcrypto_ChaCha20Poly1305_locals_dict_table",
            "embed/extmod/modtrezorcrypto/modtrezorcrypto-chacha20poly1305.h",
        ),
        (
            "mod_trezorcrypto_bip32_globals",
            "embed/extmod/modtrezorcrypto/modtrezorcrypto-bip32.h",
        ),
        (
            "mp_module_trezorui_globals",
            "embed/extmod/modtrezorui/modtrezorui.c",
        ),
        (
            "ed25519_sign_open",
            "vendor/trezor-crypto/ed25519-donna/ed25519.h",
        ),
        (
            "aes_decrypt_key192",
            "vendor/trezor-crypto/aes/aesopt.h",
        ),
        (
            "mp_type_RuntimeError",
            "vendor/micropython/py/obj.h",
        ),
        (
            "mod_binascii_a2b_base64_obj",
            "vendor/micropython/extmod/modubinascii.c",
        ),
        (
            "mp_math_floor",
            "vendor/micropython/py/modmath.c",
        ),
    ],
)
def test_get_definition(func: str, definition: str):
    assert CR._get_definition(mock_data_row(func_name=func)) == definition


@pytest.mark.parametrize(
    "line_with_SYMBOL",
    [
        "const secp256k1_ge_storage SYMBOL[ECMULT_GEN_PREC_N(ECMULT_GEN_PREC_BITS)][ECMULT_GEN_PREC_G(ECMULT_GEN_PREC_BITS)] = {",
        "void SYMBOL(bignum25519 out, const bignum25519 a, const bignum25519 b) {",
        "const qstr_pool_t SYMBOL = {",
        "} SYMBOL[WORDS_COUNT] = {",
        "static const char* const SYMBOL[WORDS_COUNT] = {",
        "	float SYMBOL(float x, float *iptr)",
        "SYMBOL(sph_groestl_big_context *sc,",
        "static uint8_t SYMBOL(USBD_HandleTypeDef *dev,",
        "AES_RETURN SYMBOL(const unsigned char *ibuf, unsigned char *obuf,",
        "secbool SYMBOL(const usb_vcp_info_t *info) {",
        "const uint8_t ALIGN(16) SYMBOL[256][96] = {",
        "	__int32_t SYMBOL(float x, float *y)",
        "        int SYMBOL(float *x, float *y, int e0, int nx, int prec, const __uint8_t *ipio2)",
        "STATIC vstr_t SYMBOL(const char *str, const char *top, int *arg_i, size_t n_args, const mp_obj_t *args, mp_map_t *kwargs) {",
        "SECP256K1_INLINE static void SYMBOL(uint64_t *r, const uint64_t *a) {",
        "static const sph_u32 SYMBOL[] = {",
        "uint32_t SYMBOL(void) {",
        "char *SYMBOL(char **buf, size_t *buf_size, size_t *fmt_size, mp_const_obj_t self_in,",
        "char* SYMBOL(const sha2_byte* data, size_t len, char digest[SHA1_DIGEST_STRING_LENGTH]) {",
        "void *SYMBOL(void *ptr_in, size_t n_bytes, bool allow_move) {",
        "const uint8_t ALIGN(16) SYMBOL[256][96] = {",
        "mp_uint_t SYMBOL(const byte *s, const byte *ptr) {",
        "static const secp256k1_fe SYMBOL = SECP256K1_FE_CONST(0, 0, 0, 0, 0, 0, 0, 1);",
        "size_t SYMBOL(size_t inlen) {",
        "FRESULT SYMBOL (    /* FR_OK(0): successful, !=0: error code */",
        "qstr SYMBOL(const char *str, size_t len) {",
        "DRESULT SYMBOL(void) {",
        "USBD_StatusTypeDef  SYMBOL   (USBD_HandleTypeDef *pdev)",
        "DWORD SYMBOL ( /* Returns up-converted code point */",
        "HAL_StatusTypeDef SYMBOL(I2C_HandleTypeDef *hi2c, uint16_t DevAddress, uint8_t *pData, uint16_t Size, uint32_t Timeout)",
    ],
)
def test_validate_line_for_definition_true(line_with_SYMBOL: str):
    assert validate_line_for_definition(line_with_SYMBOL, "SYMBOL") is True


@pytest.mark.parametrize(
    "line_with_SYMBOL",
    [
        "extern const mp_obj_type_t SYMBOL;",
    ],
)
def test_validate_line_for_definition_accept_declaration(line_with_SYMBOL: str):
    assert (
        validate_line_for_definition(
            line_with_SYMBOL, "SYMBOL", accept_declaration=True
        )
        is True
    )
    assert (
        validate_line_for_definition(
            line_with_SYMBOL, "SYMBOL", accept_declaration=False
        )
        is False
    )


@pytest.mark.parametrize(
    "symbol,line",
    [
        (
            "Font_Roboto_Regular_20_glyph_88",
            "/* X */ static const uint8_t Font_Roboto_Regular_20_glyph_88[] = { 13, 15, 13, 0, ",
        ),
        (
            "zkp_context_acquire_writable",
            "secp256k1_context *zkp_context_acquire_writable() {",
        ),
    ],
)
def test_validate_line_for_definition_special_true(symbol: str, line: str):
    assert validate_line_for_definition(line, symbol) is True


@pytest.mark.parametrize(
    "line_with_SYMBOL",
    [
        "static secp256k1_ge_storage SYMBOL[ECMULT_GEN_PREC_N(ECMULT_GEN_PREC_BITS)][ECMULT_GEN_PREC_G(ECMULT_GEN_PREC_BITS)];",
        " * The prec values are stored in SYMBOL[i][n_i] = n_i * (PREC_G)^i * G + U_i.,",
        '    fprintf(fp, "const secp256k1_ge_storage SYMBOL[ECMULT_GEN_PREC_N(ECMULT_GEN_PREC_BITS)][ECMULT_GEN_PREC_G(ECMULT_GEN_PREC_BITS)] = {\n");',
        "extern const secp256k1_ge_storage SYMBOL[ECMULT_GEN_PREC_N(ECMULT_GEN_PREC_BITS)][ECMULT_GEN_PREC_G(ECMULT_GEN_PREC_BITS)];",
        "extern const ecdsa_curve SYMBOL;",
        "#define SYMBOL(expr) ((expr) ? (void)0 : __assert_func(__FILE__, __LINE__, __func__, #expr))",
        "// uses SYMBOL curve",
        "extern const ecdsa_curve SYMBOL;",
        " * that require BER encoded keys. When working with SYMBOL-specific",
        "    return SYMBOL[index]",
        "extern const qstr_pool_t SYMBOL;",
        "  if (sequence <= SYMBOL[0].sequence) {",
        "  return slip39_SYMBOL[words_button_seq[i].index];",
        "static int secp256k1_schnorrsig_sign_internal(unsigned char *sig64, const SYMBOL* ctx) {",
        "    while ((characteristic_obj = SYMBOL(iterable)) != MP_OBJ_STOP_ITERATION) {",
    ],
)
def test_validate_line_for_definition_false(line_with_SYMBOL: str):
    assert validate_line_for_definition(line_with_SYMBOL, "SYMBOL") is False
