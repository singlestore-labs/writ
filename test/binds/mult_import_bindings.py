from abc import abstractmethod
import ctypes
from typing import Any
import wasmtime

try:
    from typing import Protocol
except ImportError:
    class Protocol: # type: ignore
        pass


def _clamp(i: int, min: int, max: int) -> int:
    if i < min or i > max:
        raise OverflowError(f'must be between {min} and {max}')
    return i

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
class Mult:
    instance: wasmtime.Instance
    _canonical_abi_free: wasmtime.Func
    _memory: wasmtime.Memory
    _mult: wasmtime.Func
    _wit_source_get: wasmtime.Func
    _wit_source_print: wasmtime.Func
    def __init__(self, store: wasmtime.Store, linker: wasmtime.Linker, module: wasmtime.Module):
        self.instance = linker.instantiate(store, module)
        exports = self.instance.exports(store)
        
        canonical_abi_free = exports['canonical_abi_free']
        assert(isinstance(canonical_abi_free, wasmtime.Func))
        self._canonical_abi_free = canonical_abi_free
        
        memory = exports['memory']
        assert(isinstance(memory, wasmtime.Memory))
        self._memory = memory
        
        mult = exports['mult']
        assert(isinstance(mult, wasmtime.Func))
        self._mult = mult
        
        wit_source_get = exports['wit-source-get']
        assert(isinstance(wit_source_get, wasmtime.Func))
        self._wit_source_get = wit_source_get
        
        wit_source_print = exports['wit-source-print']
        assert(isinstance(wit_source_print, wasmtime.Func))
        self._wit_source_print = wit_source_print
    def mult(self, caller: wasmtime.Store, num1: int, num2: int) -> int:
        ret = self._mult(caller, _clamp(num1, -2147483648, 2147483647), _clamp(num2, -2147483648, 2147483647))
        assert(isinstance(ret, int))
        return ret
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
