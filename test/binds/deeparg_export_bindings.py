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
class DeepestInput:
    name: str
    id: int
    num: float

@dataclass
class DeeperInput:
    id: int
    rec1: DeepestInput
    arr: List[DeepestInput]
    name: str
    rec2: DeepestInput

@dataclass
class DeepInput:
    name: str
    arr: List[DeeperInput]
    rec: DeeperInput

class Deeparg(Protocol):
    @abstractmethod
    def deeparg(self, input1: DeepInput, input2: DeeperInput, input3: DeepestInput) -> int:
        raise NotImplementedError
    @abstractmethod
    def wit_source_get(self) -> str:
        raise NotImplementedError
    @abstractmethod
    def wit_source_print(self) -> None:
        raise NotImplementedError

def add_deeparg_to_linker(linker: wasmtime.Linker, store: wasmtime.Store, host: Deeparg) -> None:
    ty = wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()])
    def deeparg(caller: wasmtime.Caller, arg0: int) -> int:
        m = caller["memory"]
        assert(isinstance(m, wasmtime.Memory))
        memory = cast(wasmtime.Memory, m)
        load = _load(ctypes.c_int32, memory, caller, arg0, 0)
        load0 = _load(ctypes.c_int32, memory, caller, arg0, 4)
        ptr = load
        len1 = load0
        load2 = _load(ctypes.c_int32, memory, caller, arg0, 8)
        load3 = _load(ctypes.c_int32, memory, caller, arg0, 12)
        ptr34 = load2
        len35 = load3
        result36: List[DeeperInput] = []
        for i37 in range(0, len35):
            base4 = ptr34 + i37 * 72
            load5 = _load(ctypes.c_int32, memory, caller, base4, 0)
            load6 = _load(ctypes.c_int32, memory, caller, base4, 8)
            load7 = _load(ctypes.c_int32, memory, caller, base4, 12)
            ptr8 = load6
            len9 = load7
            load10 = _load(ctypes.c_int64, memory, caller, base4, 16)
            load11 = _load(ctypes.c_float, memory, caller, base4, 24)
            load12 = _load(ctypes.c_int32, memory, caller, base4, 32)
            load13 = _load(ctypes.c_int32, memory, caller, base4, 36)
            ptr21 = load12
            len22 = load13
            result: List[DeepestInput] = []
            for i23 in range(0, len22):
                base14 = ptr21 + i23 * 24
                load15 = _load(ctypes.c_int32, memory, caller, base14, 0)
                load16 = _load(ctypes.c_int32, memory, caller, base14, 4)
                ptr17 = load15
                len18 = load16
                load19 = _load(ctypes.c_int64, memory, caller, base14, 8)
                load20 = _load(ctypes.c_float, memory, caller, base14, 16)
                result.append(DeepestInput(_decode_utf8(memory, caller, ptr17, len18), load19, load20))
            load24 = _load(ctypes.c_int32, memory, caller, base4, 40)
            load25 = _load(ctypes.c_int32, memory, caller, base4, 44)
            ptr26 = load24
            len27 = load25
            load28 = _load(ctypes.c_int32, memory, caller, base4, 48)
            load29 = _load(ctypes.c_int32, memory, caller, base4, 52)
            ptr30 = load28
            len31 = load29
            load32 = _load(ctypes.c_int64, memory, caller, base4, 56)
            load33 = _load(ctypes.c_float, memory, caller, base4, 64)
            result36.append(DeeperInput(load5, DeepestInput(_decode_utf8(memory, caller, ptr8, len9), load10, load11), result, _decode_utf8(memory, caller, ptr26, len27), DeepestInput(_decode_utf8(memory, caller, ptr30, len31), load32, load33)))
        load38 = _load(ctypes.c_int32, memory, caller, arg0, 16)
        load39 = _load(ctypes.c_int32, memory, caller, arg0, 24)
        load40 = _load(ctypes.c_int32, memory, caller, arg0, 28)
        ptr41 = load39
        len42 = load40
        load43 = _load(ctypes.c_int64, memory, caller, arg0, 32)
        load44 = _load(ctypes.c_float, memory, caller, arg0, 40)
        load45 = _load(ctypes.c_int32, memory, caller, arg0, 48)
        load46 = _load(ctypes.c_int32, memory, caller, arg0, 52)
        ptr54 = load45
        len55 = load46
        result56: List[DeepestInput] = []
        for i57 in range(0, len55):
            base47 = ptr54 + i57 * 24
            load48 = _load(ctypes.c_int32, memory, caller, base47, 0)
            load49 = _load(ctypes.c_int32, memory, caller, base47, 4)
            ptr50 = load48
            len51 = load49
            load52 = _load(ctypes.c_int64, memory, caller, base47, 8)
            load53 = _load(ctypes.c_float, memory, caller, base47, 16)
            result56.append(DeepestInput(_decode_utf8(memory, caller, ptr50, len51), load52, load53))
        load58 = _load(ctypes.c_int32, memory, caller, arg0, 56)
        load59 = _load(ctypes.c_int32, memory, caller, arg0, 60)
        ptr60 = load58
        len61 = load59
        load62 = _load(ctypes.c_int32, memory, caller, arg0, 64)
        load63 = _load(ctypes.c_int32, memory, caller, arg0, 68)
        ptr64 = load62
        len65 = load63
        load66 = _load(ctypes.c_int64, memory, caller, arg0, 72)
        load67 = _load(ctypes.c_float, memory, caller, arg0, 80)
        load68 = _load(ctypes.c_int32, memory, caller, arg0, 88)
        load69 = _load(ctypes.c_int32, memory, caller, arg0, 96)
        load70 = _load(ctypes.c_int32, memory, caller, arg0, 100)
        ptr71 = load69
        len72 = load70
        load73 = _load(ctypes.c_int64, memory, caller, arg0, 104)
        load74 = _load(ctypes.c_float, memory, caller, arg0, 112)
        load75 = _load(ctypes.c_int32, memory, caller, arg0, 120)
        load76 = _load(ctypes.c_int32, memory, caller, arg0, 124)
        ptr84 = load75
        len85 = load76
        result86: List[DeepestInput] = []
        for i87 in range(0, len85):
            base77 = ptr84 + i87 * 24
            load78 = _load(ctypes.c_int32, memory, caller, base77, 0)
            load79 = _load(ctypes.c_int32, memory, caller, base77, 4)
            ptr80 = load78
            len81 = load79
            load82 = _load(ctypes.c_int64, memory, caller, base77, 8)
            load83 = _load(ctypes.c_float, memory, caller, base77, 16)
            result86.append(DeepestInput(_decode_utf8(memory, caller, ptr80, len81), load82, load83))
        load88 = _load(ctypes.c_int32, memory, caller, arg0, 128)
        load89 = _load(ctypes.c_int32, memory, caller, arg0, 132)
        ptr90 = load88
        len91 = load89
        load92 = _load(ctypes.c_int32, memory, caller, arg0, 136)
        load93 = _load(ctypes.c_int32, memory, caller, arg0, 140)
        ptr94 = load92
        len95 = load93
        load96 = _load(ctypes.c_int64, memory, caller, arg0, 144)
        load97 = _load(ctypes.c_float, memory, caller, arg0, 152)
        load98 = _load(ctypes.c_int32, memory, caller, arg0, 160)
        load99 = _load(ctypes.c_int32, memory, caller, arg0, 164)
        ptr100 = load98
        len101 = load99
        load102 = _load(ctypes.c_int64, memory, caller, arg0, 168)
        load103 = _load(ctypes.c_float, memory, caller, arg0, 176)
        ret = host.deeparg(DeepInput(_decode_utf8(memory, caller, ptr, len1), result36, DeeperInput(load38, DeepestInput(_decode_utf8(memory, caller, ptr41, len42), load43, load44), result56, _decode_utf8(memory, caller, ptr60, len61), DeepestInput(_decode_utf8(memory, caller, ptr64, len65), load66, load67))), DeeperInput(load68, DeepestInput(_decode_utf8(memory, caller, ptr71, len72), load73, load74), result86, _decode_utf8(memory, caller, ptr90, len91), DeepestInput(_decode_utf8(memory, caller, ptr94, len95), load96, load97)), DeepestInput(_decode_utf8(memory, caller, ptr100, len101), load102, load103))
        return _clamp(ret, -2147483648, 2147483647)
    linker.define('deeparg', 'deeparg', wasmtime.Func(store, ty, deeparg, access_caller = True))
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
    linker.define('deeparg', 'wit-source-get', wasmtime.Func(store, ty, wit_source_get, access_caller = True))
    ty = wasmtime.FuncType([], [])
    def wit_source_print(caller: wasmtime.Caller) -> None:
        host.wit_source_print()
    linker.define('deeparg', 'wit-source-print', wasmtime.Func(store, ty, wit_source_print, access_caller = True))
