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

def _list_canon_lift(ptr: int, len: int, size: int, ty: Any, mem: wasmtime.Memory ,store: wasmtime.Storelike) -> Any:
    ptr = ptr & 0xffffffff
    len = len & 0xffffffff
    if ptr + len * size > mem.data_len(store):
        raise IndexError('list out of bounds')
    raw_base = mem.data_ptr(store)
    base = ctypes.POINTER(ty)(
        ty.from_address(ctypes.addressof(raw_base.contents) + ptr)
    )
    if ty == ctypes.c_uint8:
        return ctypes.string_at(base, len)
    return base[:len]
@dataclass
class HilbertInput:
    vec: bytes
    min_value: float
    max_value: float
    scale: float

@dataclass
class HilbertOutput:
    idx: str

class Hilbert(Protocol):
    @abstractmethod
    def hilbert_encode(self, input: HilbertInput) -> List[HilbertOutput]:
        raise NotImplementedError
    @abstractmethod
    def wit_source_get(self) -> str:
        raise NotImplementedError
    @abstractmethod
    def wit_source_print(self) -> None:
        raise NotImplementedError

def add_hilbert_to_linker(linker: wasmtime.Linker, store: wasmtime.Store, host: Hilbert) -> None:
    ty = wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.f64(), wasmtime.ValType.f64(), wasmtime.ValType.f64(), wasmtime.ValType.i32()], [])
    def hilbert_encode(caller: wasmtime.Caller, arg0: int, arg1: int, arg2: float, arg3: float, arg4: float, arg5: int) -> None:
        m = caller["memory"]
        assert(isinstance(m, wasmtime.Memory))
        memory = cast(wasmtime.Memory, m)
        realloc = caller["canonical_abi_realloc"]
        assert(isinstance(realloc, wasmtime.Func))
        ptr = arg0
        len0 = arg1
        ret = host.hilbert_encode(HilbertInput(cast(bytes, _list_canon_lift(ptr, len0, 1, ctypes.c_uint8, memory, caller)), arg2, arg3, arg4))
        vec = ret
        len4 = len(vec)
        result = realloc(caller, 0, 0, 4, len4 * 8)
        assert(isinstance(result, int))
        for i5 in range(0, len4):
            e = vec[i5]
            base1 = result + i5 * 8
            record = e
            field = record.idx
            ptr2, len3 = _encode_utf8(field, realloc, memory, caller)
            _store(ctypes.c_uint32, memory, caller, base1, 4, len3)
            _store(ctypes.c_uint32, memory, caller, base1, 0, ptr2)
        _store(ctypes.c_uint32, memory, caller, arg5, 4, len4)
        _store(ctypes.c_uint32, memory, caller, arg5, 0, result)
    linker.define('hilbert', 'hilbert-encode', wasmtime.Func(store, ty, hilbert_encode, access_caller = True))
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
    linker.define('hilbert', 'wit-source-get', wasmtime.Func(store, ty, wit_source_get, access_caller = True))
    ty = wasmtime.FuncType([], [])
    def wit_source_print(caller: wasmtime.Caller) -> None:
        host.wit_source_print()
    linker.define('hilbert', 'wit-source-print', wasmtime.Func(store, ty, wit_source_print, access_caller = True))
