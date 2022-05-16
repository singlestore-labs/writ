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


def _clamp(i: int, min: int, max: int) -> int:
    if i < min or i > max:
        raise OverflowError(f'must be between {min} and {max}')
    return i

def _store(ty: Any, mem: wasmtime.Memory, store: wasmtime.Storelike, base: int, offset: int, val: Any) -> None:
    ptr = (base & 0xffffffff) + offset
    if ptr + ctypes.sizeof(ty) > mem.data_len(store):
        raise IndexError('out-of-bounds store')
    raw_base = mem.data_ptr(store)
    c_ptr = ctypes.POINTER(ty)(
        ty.from_address(ctypes.addressof(raw_base.contents) + ptr)
    )
    c_ptr[0] = val

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
class Bar:
    name: str
    age: int

class Record:
    instance: wasmtime.Instance
    _canonical_abi_realloc: wasmtime.Func
    _memory: wasmtime.Memory
    _test_list_record: wasmtime.Func
    def __init__(self, store: wasmtime.Store, linker: wasmtime.Linker, module: wasmtime.Module):
        self.instance = linker.instantiate(store, module)
        exports = self.instance.exports(store)
        
        canonical_abi_realloc = exports['canonical_abi_realloc']
        assert(isinstance(canonical_abi_realloc, wasmtime.Func))
        self._canonical_abi_realloc = canonical_abi_realloc
        
        memory = exports['memory']
        assert(isinstance(memory, wasmtime.Memory))
        self._memory = memory
        
        test_list_record = exports['test-list-record']
        assert(isinstance(test_list_record, wasmtime.Func))
        self._test_list_record = test_list_record
    def test_list_record(self, caller: wasmtime.Store, a: List[Bar]) -> int:
        memory = self._memory;
        realloc = self._canonical_abi_realloc
        vec = a
        len3 = len(vec)
        result = realloc(caller, 0, 0, 4, len3 * 12)
        assert(isinstance(result, int))
        for i4 in range(0, len3):
            e = vec[i4]
            base0 = result + i4 * 12
            record = e
            field = record.name
            field1 = record.age
            ptr, len2 = _encode_utf8(field, realloc, memory, caller)
            _store(ctypes.c_uint32, memory, caller, base0, 4, len2)
            _store(ctypes.c_uint32, memory, caller, base0, 0, ptr)
            _store(ctypes.c_uint32, memory, caller, base0, 8, _clamp(field1, -2147483648, 2147483647))
        ret = self._test_list_record(caller, result, len3)
        assert(isinstance(ret, int))
        return ret
