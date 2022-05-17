from abc import abstractmethod
import ctypes
from dataclasses import dataclass
from typing import Any, Tuple
import wasmtime

try:
    from typing import Protocol
except ImportError:
    class Protocol: # type: ignore
        pass


def _load(ty: Any, mem: wasmtime.Memory, store: wasmtime.Storelike, base: int, offset: int) -> Any:
    ptr = (base & 0xffffffff) + offset
    if ptr + ctypes.sizeof(ty) > mem.data_len(store):
        raise IndexError('out-of-bounds store')
    raw_base = mem.data_ptr(store)
    c_ptr = ctypes.POINTER(ty)(
        ty.from_address(ctypes.addressof(raw_base.contents) + ptr)
    )
    return c_ptr[0]

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

class Sentiment:
    instance: wasmtime.Instance
    _canonical_abi_free: wasmtime.Func
    _canonical_abi_realloc: wasmtime.Func
    _memory: wasmtime.Memory
    _sentiment: wasmtime.Func
    _wit_source_get: wasmtime.Func
    _wit_source_print: wasmtime.Func
    def __init__(self, store: wasmtime.Store, linker: wasmtime.Linker, module: wasmtime.Module):
        self.instance = linker.instantiate(store, module)
        exports = self.instance.exports(store)
        
        canonical_abi_free = exports['canonical_abi_free']
        assert(isinstance(canonical_abi_free, wasmtime.Func))
        self._canonical_abi_free = canonical_abi_free
        
        canonical_abi_realloc = exports['canonical_abi_realloc']
        assert(isinstance(canonical_abi_realloc, wasmtime.Func))
        self._canonical_abi_realloc = canonical_abi_realloc
        
        memory = exports['memory']
        assert(isinstance(memory, wasmtime.Memory))
        self._memory = memory
        
        sentiment = exports['sentiment']
        assert(isinstance(sentiment, wasmtime.Func))
        self._sentiment = sentiment
        
        wit_source_get = exports['wit-source-get']
        assert(isinstance(wit_source_get, wasmtime.Func))
        self._wit_source_get = wit_source_get
        
        wit_source_print = exports['wit-source-print']
        assert(isinstance(wit_source_print, wasmtime.Func))
        self._wit_source_print = wit_source_print
    def sentiment(self, caller: wasmtime.Store, input: str) -> PolarityScores:
        memory = self._memory;
        realloc = self._canonical_abi_realloc
        ptr, len0 = _encode_utf8(input, realloc, memory, caller)
        ret = self._sentiment(caller, ptr, len0)
        assert(isinstance(ret, int))
        load = _load(ctypes.c_double, memory, caller, ret, 0)
        load1 = _load(ctypes.c_double, memory, caller, ret, 8)
        load2 = _load(ctypes.c_double, memory, caller, ret, 16)
        load3 = _load(ctypes.c_double, memory, caller, ret, 24)
        return PolarityScores(load, load1, load2, load3)
    def wit_source_get(self, caller: wasmtime.Store) -> str:
        memory = self._memory;
        free = self._canonical_abi_free
        ret = self._wit_source_get(caller)
        assert(isinstance(ret, int))
        load = _load(ctypes.c_int32, memory, caller, ret, 0)
        load0 = _load(ctypes.c_int32, memory, caller, ret, 4)
        ptr = load
        len1 = load0
        list = _decode_utf8(memory, caller, ptr, len1)
        free(caller, ptr, len1, 1)
        return list
    def wit_source_print(self, caller: wasmtime.Store) -> None:
        self._wit_source_print(caller)
        return 
