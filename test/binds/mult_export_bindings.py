from abc import abstractmethod
import ctypes
from typing import Any, Tuple, cast
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
class Mult(Protocol):
    @abstractmethod
    def mult(self, num1: int, num2: int) -> int:
        raise NotImplementedError
    @abstractmethod
    def wit_source_get(self) -> str:
        raise NotImplementedError
    @abstractmethod
    def wit_source_print(self) -> None:
        raise NotImplementedError

def add_mult_to_linker(linker: wasmtime.Linker, store: wasmtime.Store, host: Mult) -> None:
    ty = wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32()], [wasmtime.ValType.i32()])
    def mult(caller: wasmtime.Caller, arg0: int, arg1: int) -> int:
        ret = host.mult(arg0, arg1)
        return _clamp(ret, -2147483648, 2147483647)
    linker.define('mult', 'mult', wasmtime.Func(store, ty, mult, access_caller = True))
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
    linker.define('mult', 'wit-source-get', wasmtime.Func(store, ty, wit_source_get, access_caller = True))
    ty = wasmtime.FuncType([], [])
    def wit_source_print(caller: wasmtime.Caller) -> None:
        host.wit_source_print()
    linker.define('mult', 'wit-source-print', wasmtime.Func(store, ty, wit_source_print, access_caller = True))
