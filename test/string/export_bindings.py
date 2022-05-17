from abc import abstractmethod
import ctypes
from dataclasses import dataclass
from typing import Any, List, Tuple, cast
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
class Subphrase:
    str: str
    idx: int

class Split(Protocol):
    @abstractmethod
    def split_str(self, phrase: str, delim: str) -> List[Subphrase]:
        raise NotImplementedError

def add_split_to_linker(linker: wasmtime.Linker, store: wasmtime.Store, host: Split) -> None:
    ty = wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32()], [])
    def split_str(caller: wasmtime.Caller, arg0: int, arg1: int, arg2: int, arg3: int, arg4: int) -> None:
        m = caller["memory"]
        assert(isinstance(m, wasmtime.Memory))
        memory = cast(wasmtime.Memory, m)
        realloc = caller["canonical_abi_realloc"]
        assert(isinstance(realloc, wasmtime.Func))
        ptr = arg0
        len0 = arg1
        ptr1 = arg2
        len2 = arg3
        ret = host.split_str(_decode_utf8(memory, caller, ptr, len0), _decode_utf8(memory, caller, ptr1, len2))
        vec = ret
        len7 = len(vec)
        result = realloc(caller, 0, 0, 4, len7 * 12)
        assert(isinstance(result, int))
        for i8 in range(0, len7):
            e = vec[i8]
            base3 = result + i8 * 12
            record = e
            field = record.str
            field4 = record.idx
            ptr5, len6 = _encode_utf8(field, realloc, memory, caller)
            _store(ctypes.c_uint32, memory, caller, base3, 4, len6)
            _store(ctypes.c_uint32, memory, caller, base3, 0, ptr5)
            _store(ctypes.c_uint32, memory, caller, base3, 8, _clamp(field4, -2147483648, 2147483647))
        _store(ctypes.c_uint32, memory, caller, arg4, 4, len7)
        _store(ctypes.c_uint32, memory, caller, arg4, 0, result)
    linker.define('split', 'split-str', wasmtime.Func(store, ty, split_str, access_caller = True))
