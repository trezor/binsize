from binsize.lib.data_loader import BloatyDataLoader

from .common import BLOATY_MOCK_CSV, mock_data_row


def test_load_csv():
    row_data = BloatyDataLoader().load_data_from_csv(BLOATY_MOCK_CSV)
    assert len(row_data) == 7
    assert row_data == [
        mock_data_row(
            section=".flash2", symbol_name="secp256k1_ecmult_gen_prec_table", size=65536
        ),
        mock_data_row(
            section=".flash2",
            symbol_name="fun_data_apps_ethereum_tokens__lt_module_gt__token_by_chain_address",
            size=36857,
        ),
        mock_data_row(
            section=".flash2", symbol_name="mp_qstr_frozen_const_pool", size=27520
        ),
        mock_data_row(section=".flash2", symbol_name="mp_frozen_mpy_names", size=10461),
        mock_data_row(section=".flash", symbol_name="nist256p1", size=37084),
        mock_data_row(
            section=".flash", symbol_name="ge25519_niels_base_multiples", size=24576
        ),
        mock_data_row(
            section=".flash",
            symbol_name="trezor_lib::protobuf::decode::Decoder::decode_field::hab425281b2042fd5",
            size=1116,
        ),
    ]
