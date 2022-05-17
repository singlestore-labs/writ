from abc import abstractmethod
import ctypes
from dataclasses import dataclass
from typing import Any, List, Tuple
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
class TokenizeInput:
    s: str
    delimiter: str

@dataclass
class TokenizeOutput:
    c: str

class Tokenize:
    instance: wasmtime.Instance
    _canonical_abi_free: wasmtime.Func
    _canonical_abi_realloc: wasmtime.Func
    _memory: wasmtime.Memory
    _tokenize: wasmtime.Func
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
        
        tokenize = exports['tokenize']
        assert(isinstance(tokenize, wasmtime.Func))
        self._tokenize = tokenize
        
        wit_source_get = exports['wit-source-get']
        assert(isinstance(wit_source_get, wasmtime.Func))
        self._wit_source_get = wit_source_get
        
        wit_source_print = exports['wit-source-print']
        assert(isinstance(wit_source_print, wasmtime.Func))
        self._wit_source_print = wit_source_print
    def tokenize(self, caller: wasmtime.Store, input: TokenizeInput) -> List[TokenizeOutput]:
        memory = self._memory;
        realloc = self._canonical_abi_realloc
        free = self._canonical_abi_free
        record = input
        field = record.s
        field0 = record.delimiter
        ptr, len1 = _encode_utf8(field, realloc, memory, caller)
        ptr2, len3 = _encode_utf8(field0, realloc, memory, caller)
        ret = self._tokenize(caller, ptr, len1, ptr2, len3)
        assert(isinstance(ret, int))
        load = _load(ctypes.c_int32, memory, caller, ret, 0)
        load4 = _load(ctypes.c_int32, memory, caller, ret, 4)
        ptr10 = load
        len11 = load4
        result: List[TokenizeOutput] = []
        for i12 in range(0, len11):
            base5 = ptr10 + i12 * 8
            load6 = _load(ctypes.c_int32, memory, caller, base5, 0)
            load7 = _load(ctypes.c_int32, memory, caller, base5, 4)
            ptr8 = load6
            len9 = load7
            list = _decode_utf8(memory, caller, ptr8, len9)
            free(caller, ptr8, len9, 1)
            result.append(TokenizeOutput(list))
        free(caller, ptr10, len11 * 8, 4)
        return result
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
