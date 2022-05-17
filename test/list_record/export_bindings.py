from abc import abstractmethod
import ctypes
from dataclasses import dataclass
from typing import Any, List, cast
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
@dataclass
class Bar:
    name: str
    age: int

class Record(Protocol):
    @abstractmethod
    def test_list_record(self, a: List[Bar]) -> int:
        raise NotImplementedError

def add_record_to_linker(linker: wasmtime.Linker, store: wasmtime.Store, host: Record) -> None:
    ty = wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32()], [wasmtime.ValType.i32()])
    def test_list_record(caller: wasmtime.Caller, arg0: int, arg1: int) -> int:
        m = caller["memory"]
        assert(isinstance(m, wasmtime.Memory))
        memory = cast(wasmtime.Memory, m)
        ptr4 = arg0
        len5 = arg1
        result: List[Bar] = []
        for i6 in range(0, len5):
            base0 = ptr4 + i6 * 12
            load = _load(ctypes.c_int32, memory, caller, base0, 0)
            load1 = _load(ctypes.c_int32, memory, caller, base0, 4)
            ptr = load
            len2 = load1
            load3 = _load(ctypes.c_int32, memory, caller, base0, 8)
            result.append(Bar(_decode_utf8(memory, caller, ptr, len2), load3))
        ret = host.test_list_record(result)
        return _clamp(ret, -2147483648, 2147483647)
    linker.define('record', 'test-list-record', wasmtime.Func(store, ty, test_list_record, access_caller = True))
