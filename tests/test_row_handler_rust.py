import pytest

from binsize.lib.row_handler_rust import (
    RustRow,
    get_real_symbol_from_alias,
    replace_dollar_encodings,
)

from .common import mock_data_row

RR = RustRow()


@pytest.mark.parametrize(
    "symbol,module,func",
    [
        (
            "trezor_lib::protobuf::decode::Decoder::decode_field::hab425281b2042fd5",
            "embed/rust/src/protobuf/decode.rs",
            "Decoder::decode_field()",
        ),
        (
            "trezor_lib::protobuf::obj::msg_obj_attr::h59281a534905240d",
            "embed/rust/src/protobuf/obj.rs",
            "msg_obj_attr()",
        ),
        (
            "trezor_lib::protobuf::nonexisting::obj::msg_obj_attr::h59281a534905240d",
            "--invalid_file--embed/rust/src/protobuf/nonexisting/obj.rs",
            "msg_obj_attr()",
        ),
        (
            "trezor_lib::micropython::list::_$LT$impl$u20$trezor_lib..micropython..ffi.._mp_obj_list_t$GT$::alloc::h988fbb6155b3d81e",
            "embed/rust/src/micropython/list.rs",
            "alloc()",
        ),
        (
            "trezor_lib::ui::util::try_or_raise::_$u7b$$u7b$closure$u7d$$u7d$::h059f3c8d3819af81",
            "embed/rust/src/ui/util.rs",
            "try_or_raise()",
        ),
        (
            "trezor_lib::protobuf::obj::MsgDefObj::obj_type::TYPE::hf415c733c642ed60",
            "embed/rust/src/protobuf/obj.rs",
            "MsgDefObj::obj_type()",
        ),
        (
            "_$LT$trezor_lib..protobuf..encode..BufferStream$u20$as$u20$trezor_lib..protobuf..encode..OutputStream$GT$::write::h070fc0f5b28d205d",
            "embed/rust/src/protobuf/encode.rs",
            "BufferStream::write()",
        ),
        (
            "_$LT$core..fmt..builders..PadAdapter$u20$as$u20$core..fmt..Write$GT$::write_str",
            "",
            "core::fmt::builders::PadAdapter::write_str()",
        ),
        (
            "_$LT$heapless..string..String$LT$_$GT$$u20$as$u20$core..fmt..Debug$GT$::fmt",
            "",
            "heapless::string::String<_>::fmt()",
        ),
        (
            "_$LT$trezor_lib..ui..component..base..Child$LT$T$GT$$u20$as$u20$trezor_lib..ui..layout..obj..ObjComponent$GT$::obj_place::hf8972368c98507f3",
            "embed/rust/src/ui/component/base.rs",
            "Child<T>::obj_place()",
        ),
        (
            "trezor_lib::micropython::ffi::_mp_map_t::used::h99711956814a49e3",
            "embed/rust/src/micropython/ffi.rs",
            "_mp_map_t::used()",
        ),
    ],
)
def test_get_module_and_function(symbol: str, module: str, func: str):
    assert RR._get_module_and_function(symbol) == (module, func)


@pytest.mark.parametrize(
    "symbol,result",
    [
        (
            "trezor_lib::micropython::list::_$LT$impl$u20$trezor_lib..micropython..ffi.._mp_obj_list_t$GT$::alloc",
            "trezor_lib::micropython::list::_<impl trezor_lib::micropython::ffi::_mp_obj_list_t>::alloc",
        ),
        (
            "_$LT$core..fmt..builders..PadAdapter$u20$as$u20$core..fmt..Write$GT$::write_str",
            "_<core::fmt::builders::PadAdapter as core::fmt::Write>::write_str",
        ),
        (
            "_$LT$core..str..iter..Split$LT$P$GT$$u20$as$u20$core..iter..traits..iterator..Iterator$GT$::next",
            "_<core::str::iter::Split<P> as core::iter::traits::iterator::Iterator>::next",
        ),
        (
            "_$LT$heapless..string..String$LT$_$GT$$u20$as$u20$core..fmt..Debug$GT$::fmt",
            "_<heapless::string::String<_> as core::fmt::Debug>::fmt",
        ),
        (
            "_$LT$trezor_lib..ui..component..base..Child$LT$T$GT$$u20$as$u20$trezor_lib..ui..layout..obj..ObjComponent$GT$::obj_place",
            "_<trezor_lib::ui::component::base::Child<T> as trezor_lib::ui::layout::obj::ObjComponent>::obj_place",
        ),
        (
            "_$LT$$RF$mut$u20$W$u20$as$u20$core..fmt..Write$GT$::write_str",
            "_<&mut W as core::fmt::Write>::write_str",
        ),
        (
            "_$LT$T$u20$as$u20$core..convert..TryInto$LT$U$GT$$GT$::try_into",
            "_<T as core::convert::TryInto<U>>::try_into",
        ),
        (
            "trezor_lib::util::try_or_raise::_$u7b$$u7b$closure$u7d$$u7d$",
            "trezor_lib::util::try_or_raise::_{{closure}}",
        ),
    ],
)
def test_replace_dollar_encodings(symbol: str, result: str):
    assert replace_dollar_encodings(symbol) == result


@pytest.mark.parametrize(
    "symbol,result",
    [
        (
            "_<core::fmt::builders::PadAdapter as core::fmt::Write>::write_str",
            "core::fmt::builders::PadAdapter::write_str",
        ),
        (
            "_<core::str::iter::Split<P> as core::iter::traits::iterator::Iterator>::next",
            "core::str::iter::Split<P>::next",
        ),
        (
            "_<heapless::string::String<_> as core::fmt::Debug>::fmt",
            "heapless::string::String<_>::fmt",
        ),
        (
            "_<trezor_lib::ui::component::base::Child<T> as trezor_lib::ui::layout::obj::ObjComponent>::obj_place",
            "trezor_lib::ui::component::base::Child<T>::obj_place",
        ),
        (
            "_<&mut W as core::fmt::Write>::write_str",
            "core::fmt::Write::write_str",
        ),
        (
            "_<T as core::convert::TryInto<U>>::try_into",
            "core::convert::TryInto<U>::try_into",
        ),
        (
            "_<usize as trezor_lib::trace::Trace>::trace",
            "trezor_lib::trace::Trace::trace",
        ),
    ],
)
def test_get_real_symbol_from_alias(symbol: str, result: str):
    assert get_real_symbol_from_alias(symbol) == result


def test_add_basic_info_row_handlers():
    new_row = RR.add_basic_info(
        mock_data_row(
            symbol_name="trezor_lib::protobuf::decode::Decoder::decode_field::hab425281b2042fd5"
        )
    )
    assert new_row.language == "Rust"
    assert new_row.module_name == "embed/rust/src/protobuf/decode.rs"
    assert new_row.func_name == "Decoder::decode_field()"


@pytest.mark.parametrize(
    "module,func,definition",
    [
        (
            "embed/rust/src/protobuf/encode.rs",
            "Encoder::encode_field()",
            "embed/rust/src/protobuf/encode.rs:86",
        ),
        (
            "embed/rust/src/protobuf/obj.rs",
            "msg_obj_attr()",
            "embed/rust/src/protobuf/obj.rs:134",
        ),
        (
            "embed/rust/src/micropython/runtime.rs",
            "trampoline()",
            "embed/rust/src/micropython/runtime.rs:68",
        ),
        (
            "embed/rust/src/protobuf/obj.rs",
            "unexisting_msg_obj_attr()",
            "",
        ),
        (
            "embed/rust/src/unexisting_protobuf/obj.rs",
            "msg_obj_attr()",
            "",
        ),
    ],
)
def test_get_definition(module: str, func: str, definition: str):
    assert (
        RR._get_definition(mock_data_row(module_name=module, func_name=func))
        == definition
    )
