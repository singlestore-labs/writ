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

class Tokenize(Protocol):
    @abstractmethod
    def tokenize(self, input: TokenizeInput) -> List[TokenizeOutput]:
        raise NotImplementedError
    @abstractmethod
    def wit_source_get(self) -> str:
        raise NotImplementedError
    @abstractmethod
    def wit_source_print(self) -> None:
        raise NotImplementedError

def add_tokenize_to_linker(linker: wasmtime.Linker, store: wasmtime.Store, host: Tokenize) -> None:
    ty = wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32()], [])
    def tokenize(caller: wasmtime.Caller, arg0: int, arg1: int, arg2: int, arg3: int, arg4: int) -> None:
        m = caller["memory"]
        assert(isinstance(m, wasmtime.Memory))
        memory = cast(wasmtime.Memory, m)
        realloc = caller["canonical_abi_realloc"]
        assert(isinstance(realloc, wasmtime.Func))
        ptr = arg0
        len0 = arg1
        ptr1 = arg2
        len2 = arg3
        ret = host.tokenize(TokenizeInput(_decode_utf8(memory, caller, ptr, len0), _decode_utf8(memory, caller, ptr1, len2)))
        vec = ret
        len6 = len(vec)
        result = realloc(caller, 0, 0, 4, len6 * 8)
        assert(isinstance(result, int))
        for i7 in range(0, len6):
            e = vec[i7]
            base3 = result + i7 * 8
            record = e
            field = record.c
            ptr4, len5 = _encode_utf8(field, realloc, memory, caller)
            _store(ctypes.c_uint32, memory, caller, base3, 4, len5)
            _store(ctypes.c_uint32, memory, caller, base3, 0, ptr4)
        _store(ctypes.c_uint32, memory, caller, arg4, 4, len6)
        _store(ctypes.c_uint32, memory, caller, arg4, 0, result)
    linker.define('tokenize', 'tokenize', wasmtime.Func(store, ty, tokenize, access_caller = True))
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
    linker.define('tokenize', 'wit-source-get', wasmtime.Func(store, ty, wit_source_get, access_caller = True))
    ty = wasmtime.FuncType([], [])
    def wit_source_print(caller: wasmtime.Caller) -> None:
        host.wit_source_print()
    linker.define('tokenize', 'wit-source-print', wasmtime.Func(store, ty, wit_source_print, access_caller = True))
