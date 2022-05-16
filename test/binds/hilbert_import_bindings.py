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

def _list_canon_lower(list: Any, ty: Any, size: int, align: int, realloc: wasmtime.Func, mem: wasmtime.Memory, store: wasmtime.Storelike) -> Tuple[int, int]:
    total_size = size * len(list)
    ptr = realloc(store, 0, 0, align, total_size)
    assert(isinstance(ptr, int))
    ptr = ptr & 0xffffffff
    if ptr + total_size > mem.data_len(store):
        raise IndexError('list realloc return of bounds')
    raw_base = mem.data_ptr(store)
    base = ctypes.POINTER(ty)(
        ty.from_address(ctypes.addressof(raw_base.contents) + ptr)
    )
    for i, val in enumerate(list):
        base[i] = val
    return (ptr, len(list))
@dataclass
class HilbertInput:
    vec: bytes
    min_value: float
    max_value: float
    scale: float

@dataclass
class HilbertOutput:
    idx: str

class Hilbert:
    instance: wasmtime.Instance
    _canonical_abi_free: wasmtime.Func
    _canonical_abi_realloc: wasmtime.Func
    _hilbert_encode: wasmtime.Func
    _memory: wasmtime.Memory
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
        
        hilbert_encode = exports['hilbert-encode']
        assert(isinstance(hilbert_encode, wasmtime.Func))
        self._hilbert_encode = hilbert_encode
        
        memory = exports['memory']
        assert(isinstance(memory, wasmtime.Memory))
        self._memory = memory
        
        wit_source_get = exports['wit-source-get']
        assert(isinstance(wit_source_get, wasmtime.Func))
        self._wit_source_get = wit_source_get
        
        wit_source_print = exports['wit-source-print']
        assert(isinstance(wit_source_print, wasmtime.Func))
        self._wit_source_print = wit_source_print
    def hilbert_encode(self, caller: wasmtime.Store, input: HilbertInput) -> List[HilbertOutput]:
        memory = self._memory;
        realloc = self._canonical_abi_realloc
        free = self._canonical_abi_free
        record = input
        field = record.vec
        field0 = record.min_value
        field1 = record.max_value
        field2 = record.scale
        ptr, len3 = _list_canon_lower(field, ctypes.c_uint8, 1, 1, realloc, memory, caller)
        ret = self._hilbert_encode(caller, ptr, len3, field0, field1, field2)
        assert(isinstance(ret, int))
        load = _load(ctypes.c_int32, memory, caller, ret, 0)
        load4 = _load(ctypes.c_int32, memory, caller, ret, 4)
        ptr10 = load
        len11 = load4
        result: List[HilbertOutput] = []
        for i12 in range(0, len11):
            base5 = ptr10 + i12 * 8
            load6 = _load(ctypes.c_int32, memory, caller, base5, 0)
            load7 = _load(ctypes.c_int32, memory, caller, base5, 4)
            ptr8 = load6
            len9 = load7
            list = _decode_utf8(memory, caller, ptr8, len9)
            free(caller, ptr8, len9, 1)
            result.append(HilbertOutput(list))
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
