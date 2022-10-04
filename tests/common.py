from binsize.lib.api import DataRow
from binsize.lib.binary_size import BinarySize
from binsize.lib.data_handler import RowHandlerFactory
from binsize.lib.data_loader import BloatyDataLoader

BLOATY_MOCK_CSV = """
sections,symbols,vmsize,filesize
.flash2,secp256k1_ecmult_gen_prec_table,65536,65536
.flash2,fun_data_apps_ethereum_tokens__lt_module_gt__token_by_chain_address,36857,36857
.flash2,mp_qstr_frozen_const_pool,27520,27520
.flash2,mp_frozen_mpy_names,10461,10461
.flash,nist256p1,37084,37084
.flash,ge25519_niels_base_multiples,24576,24576
.flash,trezor_lib::protobuf::decode::Decoder::decode_field::hab425281b2042fd5,1116,1116
""".strip()


def get_bloaty_BS() -> BinarySize:
    return BinarySize(
        data_loader=BloatyDataLoader(), row_handler_factory=RowHandlerFactory()
    )


def mock_data_row(
    symbol_name: str = "",
    module_name: str = "",
    func_name: str = "",
    language: str = "",
    section: str = "",
    size: int = 0,
    logic_size: int = 0,
    data_size: int = 0,
    number_of_symbols: int = 0,
    source_definition: str = "",
    build_definition: str = "",
) -> DataRow:
    return DataRow(
        symbol_name=symbol_name,
        module_name=module_name,
        func_name=func_name,
        language=language,
        section=section,
        size=size,
        logic_size=logic_size,
        data_size=data_size,
        number_of_symbols=number_of_symbols,
        source_definition=source_definition,
        build_definition=build_definition,
    )
