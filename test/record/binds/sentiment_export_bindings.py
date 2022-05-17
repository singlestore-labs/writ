from abc import abstractmethod
import ctypes
from dataclasses import dataclass
from typing import Any, Tuple, cast
import wasmtime

try:
    from typing import Protocol
except ImportError:
    class Protocol: # type: ignore
        pass


def _store(ty: Any, mem: wasmtime.Memory, store: wasmtime.Storelike, base: int, offset: int, val: Any) -> None:
    ptr = (base & 0xffffffff) + offset
    if ptr + ctypes.sizeof(ty) > mem.data_len(store):
        raise IndexError('out-of-bounds store')
    raw_base = mem.data_ptr(store)
    c_ptr = ctypes.POINTER(ty)(
        ty.from_address(ctypes.addressof(raw_base.contents) + ptr)
    )
    c_ptr[0] = val

def _decode_utf8(mem: wasmtime.Memory, store: wasmtime.Storelike, ptr: int, len: int) -> str:
    ptr = ptr & 0xffffffff
    len = len & 0xffffffff
    if ptr + len > mem.data_len(store):
        raise IndexError('string out of bounds')
    base = mem.data_ptr(store)
    base = ctypes.POINTER(ctypes.c_ubyte)(
        ctypes.c_ubyte.from_address(ctypes.addressof(base.contents) + ptr)
    )
    return ctypes.string_at(base, len).decode('utf-8')

def _encode_utf8(val: str, realloc: wasmtime.Func, mem: wasmtime.Memory, store: wasmtime.Storelike) -> Tuple[int, int]:
    bytes = val.encode('utf8')
    ptr = realloc(store, 0, 0, 1, len(bytes))
    assert(isinstance(ptr, int))
    ptr = ptr & 0xffffffff
    if ptr + len(bytes) > mem.data_len(store):
        raise IndexError('string out of bounds')
    base = mem.data_ptr(store)
    base = ctypes.POINTER(ctypes.c_ubyte)(
        ctypes.c_ubyte.from_address(ctypes.addressof(base.contents) + ptr)
    )
    ctypes.memmove(base, bytes, len(bytes))
    return (ptr, len(bytes))
@dataclass
class PolarityScores:
    compound: float
    positive: float
    negative: float
    neutral: float

class Sentiment(Protocol):
    @abstractmethod
    def sentiment(self, input: str) -> PolarityScores:
        raise NotImplementedError
    @abstractmethod
    def wit_source_get(self) -> str:
        raise NotImplementedError
    @abstractmethod
    def wit_source_print(self) -> None:
        raise NotImplementedError

def add_sentiment_to_linker(linker: wasmtime.Linker, store: wasmtime.Store, host: Sentiment) -> None:
    ty = wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32()], [])
    def sentiment(caller: wasmtime.Caller, arg0: int, arg1: int, arg2: int) -> None:
        m = caller["memory"]
        assert(isinstance(m, wasmtime.Memory))
        memory = cast(wasmtime.Memory, m)
        ptr = arg0
        len0 = arg1
        ret = host.sentiment(_decode_utf8(memory, caller, ptr, len0))
        record = ret
        field = record.compound
        field1 = record.positive
        field2 = record.negative
        field3 = record.neutral
        _store(ctypes.c_double, memory, caller, arg2, 0, field)
        _store(ctypes.c_double, memory, caller, arg2, 8, field1)
        _store(ctypes.c_double, memory, caller, arg2, 16, field2)
        _store(ctypes.c_double, memory, caller, arg2, 24, field3)
    linker.define('sentiment', 'sentiment', wasmtime.Func(store, ty, sentiment, access_caller = True))
    ty = wasmtime.FuncType([wasmtime.ValType.i32()], [])
    def wit_source_get(caller: wasmtime.Caller, arg0: int) -> None:
        m = caller["memory"]
        assert(isinstance(m, wasmtime.Memory))
        memory = cast(wasmtime.Memory, m)
        realloc = caller["canonical_abi_realloc"]
        assert(isinstance(realloc, wasmtime.Func))
        ret = host.wit_source_get()
        ptr, len0 = _encode_utf8(ret, realloc, memory, caller)
        _store(ctypes.c_uint32, memory, caller, arg0, 4, len0)
        _store(ctypes.c_uint32, memory, caller, arg0, 0, ptr)
    linker.define('sentiment', 'wit-source-get', wasmtime.Func(store, ty, wit_source_get, access_caller = True))
    ty = wasmtime.FuncType([], [])
    def wit_source_print(caller: wasmtime.Caller) -> None:
        host.wit_source_print()
    linker.define('sentiment', 'wit-source-print', wasmtime.Func(store, ty, wit_source_print, access_caller = True))
