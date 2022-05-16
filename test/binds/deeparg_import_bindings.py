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

class Deeparg:
    instance: wasmtime.Instance
    _canonical_abi_free: wasmtime.Func
    _canonical_abi_realloc: wasmtime.Func
    _deeparg: wasmtime.Func
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
        
        deeparg = exports['deeparg']
        assert(isinstance(deeparg, wasmtime.Func))
        self._deeparg = deeparg
        
        memory = exports['memory']
        assert(isinstance(memory, wasmtime.Memory))
        self._memory = memory
        
        wit_source_get = exports['wit-source-get']
        assert(isinstance(wit_source_get, wasmtime.Func))
        self._wit_source_get = wit_source_get
        
        wit_source_print = exports['wit-source-print']
        assert(isinstance(wit_source_print, wasmtime.Func))
        self._wit_source_print = wit_source_print
    def deeparg(self, caller: wasmtime.Store, input1: DeepInput, input2: DeeperInput, input3: DeepestInput) -> int:
        memory = self._memory;
        realloc = self._canonical_abi_realloc
        
        ptr = realloc(caller, 0, 0, 8, 184)
        assert(isinstance(ptr, int))
        record = input1
        field = record.name
        field0 = record.arr
        field1 = record.rec
        ptr2, len3 = _encode_utf8(field, realloc, memory, caller)
        _store(ctypes.c_uint32, memory, caller, ptr, 4, len3)
        _store(ctypes.c_uint32, memory, caller, ptr, 0, ptr2)
        vec35 = field0
        len37 = len(vec35)
        result36 = realloc(caller, 0, 0, 8, len37 * 72)
        assert(isinstance(result36, int))
        for i38 in range(0, len37):
            e = vec35[i38]
            base4 = result36 + i38 * 72
            record5 = e
            field6 = record5.id
            field7 = record5.rec1
            field8 = record5.arr
            field9 = record5.name
            field10 = record5.rec2
            _store(ctypes.c_uint32, memory, caller, base4, 0, _clamp(field6, -2147483648, 2147483647))
            record11 = field7
            field12 = record11.name
            field13 = record11.id
            field14 = record11.num
            ptr15, len16 = _encode_utf8(field12, realloc, memory, caller)
            _store(ctypes.c_uint32, memory, caller, base4, 12, len16)
            _store(ctypes.c_uint32, memory, caller, base4, 8, ptr15)
            _store(ctypes.c_uint64, memory, caller, base4, 16, _clamp(field13, -9223372036854775808, 9223372036854775807))
            _store(ctypes.c_float, memory, caller, base4, 24, field14)
            vec = field8
            len25 = len(vec)
            result = realloc(caller, 0, 0, 8, len25 * 24)
            assert(isinstance(result, int))
            for i26 in range(0, len25):
                e17 = vec[i26]
                base18 = result + i26 * 24
                record19 = e17
                field20 = record19.name
                field21 = record19.id
                field22 = record19.num
                ptr23, len24 = _encode_utf8(field20, realloc, memory, caller)
                _store(ctypes.c_uint32, memory, caller, base18, 4, len24)
                _store(ctypes.c_uint32, memory, caller, base18, 0, ptr23)
                _store(ctypes.c_uint64, memory, caller, base18, 8, _clamp(field21, -9223372036854775808, 9223372036854775807))
                _store(ctypes.c_float, memory, caller, base18, 16, field22)
            _store(ctypes.c_uint32, memory, caller, base4, 36, len25)
            _store(ctypes.c_uint32, memory, caller, base4, 32, result)
            ptr27, len28 = _encode_utf8(field9, realloc, memory, caller)
            _store(ctypes.c_uint32, memory, caller, base4, 44, len28)
            _store(ctypes.c_uint32, memory, caller, base4, 40, ptr27)
            record29 = field10
            field30 = record29.name
            field31 = record29.id
            field32 = record29.num
            ptr33, len34 = _encode_utf8(field30, realloc, memory, caller)
            _store(ctypes.c_uint32, memory, caller, base4, 52, len34)
            _store(ctypes.c_uint32, memory, caller, base4, 48, ptr33)
            _store(ctypes.c_uint64, memory, caller, base4, 56, _clamp(field31, -9223372036854775808, 9223372036854775807))
            _store(ctypes.c_float, memory, caller, base4, 64, field32)
        _store(ctypes.c_uint32, memory, caller, ptr, 12, len37)
        _store(ctypes.c_uint32, memory, caller, ptr, 8, result36)
        record39 = field1
        field40 = record39.id
        field41 = record39.rec1
        field42 = record39.arr
        field43 = record39.name
        field44 = record39.rec2
        _store(ctypes.c_uint32, memory, caller, ptr, 16, _clamp(field40, -2147483648, 2147483647))
        record45 = field41
        field46 = record45.name
        field47 = record45.id
        field48 = record45.num
        ptr49, len50 = _encode_utf8(field46, realloc, memory, caller)
        _store(ctypes.c_uint32, memory, caller, ptr, 28, len50)
        _store(ctypes.c_uint32, memory, caller, ptr, 24, ptr49)
        _store(ctypes.c_uint64, memory, caller, ptr, 32, _clamp(field47, -9223372036854775808, 9223372036854775807))
        _store(ctypes.c_float, memory, caller, ptr, 40, field48)
        vec59 = field42
        len61 = len(vec59)
        result60 = realloc(caller, 0, 0, 8, len61 * 24)
        assert(isinstance(result60, int))
        for i62 in range(0, len61):
            e51 = vec59[i62]
            base52 = result60 + i62 * 24
            record53 = e51
            field54 = record53.name
            field55 = record53.id
            field56 = record53.num
            ptr57, len58 = _encode_utf8(field54, realloc, memory, caller)
            _store(ctypes.c_uint32, memory, caller, base52, 4, len58)
            _store(ctypes.c_uint32, memory, caller, base52, 0, ptr57)
            _store(ctypes.c_uint64, memory, caller, base52, 8, _clamp(field55, -9223372036854775808, 9223372036854775807))
            _store(ctypes.c_float, memory, caller, base52, 16, field56)
        _store(ctypes.c_uint32, memory, caller, ptr, 52, len61)
        _store(ctypes.c_uint32, memory, caller, ptr, 48, result60)
        ptr63, len64 = _encode_utf8(field43, realloc, memory, caller)
        _store(ctypes.c_uint32, memory, caller, ptr, 60, len64)
        _store(ctypes.c_uint32, memory, caller, ptr, 56, ptr63)
        record65 = field44
        field66 = record65.name
        field67 = record65.id
        field68 = record65.num
        ptr69, len70 = _encode_utf8(field66, realloc, memory, caller)
        _store(ctypes.c_uint32, memory, caller, ptr, 68, len70)
        _store(ctypes.c_uint32, memory, caller, ptr, 64, ptr69)
        _store(ctypes.c_uint64, memory, caller, ptr, 72, _clamp(field67, -9223372036854775808, 9223372036854775807))
        _store(ctypes.c_float, memory, caller, ptr, 80, field68)
        record71 = input2
        field72 = record71.id
        field73 = record71.rec1
        field74 = record71.arr
        field75 = record71.name
        field76 = record71.rec2
        _store(ctypes.c_uint32, memory, caller, ptr, 88, _clamp(field72, -2147483648, 2147483647))
        record77 = field73
        field78 = record77.name
        field79 = record77.id
        field80 = record77.num
        ptr81, len82 = _encode_utf8(field78, realloc, memory, caller)
        _store(ctypes.c_uint32, memory, caller, ptr, 100, len82)
        _store(ctypes.c_uint32, memory, caller, ptr, 96, ptr81)
        _store(ctypes.c_uint64, memory, caller, ptr, 104, _clamp(field79, -9223372036854775808, 9223372036854775807))
        _store(ctypes.c_float, memory, caller, ptr, 112, field80)
        vec91 = field74
        len93 = len(vec91)
        result92 = realloc(caller, 0, 0, 8, len93 * 24)
        assert(isinstance(result92, int))
        for i94 in range(0, len93):
            e83 = vec91[i94]
            base84 = result92 + i94 * 24
            record85 = e83
            field86 = record85.name
            field87 = record85.id
            field88 = record85.num
            ptr89, len90 = _encode_utf8(field86, realloc, memory, caller)
            _store(ctypes.c_uint32, memory, caller, base84, 4, len90)
            _store(ctypes.c_uint32, memory, caller, base84, 0, ptr89)
            _store(ctypes.c_uint64, memory, caller, base84, 8, _clamp(field87, -9223372036854775808, 9223372036854775807))
            _store(ctypes.c_float, memory, caller, base84, 16, field88)
        _store(ctypes.c_uint32, memory, caller, ptr, 124, len93)
        _store(ctypes.c_uint32, memory, caller, ptr, 120, result92)
        ptr95, len96 = _encode_utf8(field75, realloc, memory, caller)
        _store(ctypes.c_uint32, memory, caller, ptr, 132, len96)
        _store(ctypes.c_uint32, memory, caller, ptr, 128, ptr95)
        record97 = field76
        field98 = record97.name
        field99 = record97.id
        field100 = record97.num
        ptr101, len102 = _encode_utf8(field98, realloc, memory, caller)
        _store(ctypes.c_uint32, memory, caller, ptr, 140, len102)
        _store(ctypes.c_uint32, memory, caller, ptr, 136, ptr101)
        _store(ctypes.c_uint64, memory, caller, ptr, 144, _clamp(field99, -9223372036854775808, 9223372036854775807))
        _store(ctypes.c_float, memory, caller, ptr, 152, field100)
        record103 = input3
        field104 = record103.name
        field105 = record103.id
        field106 = record103.num
        ptr107, len108 = _encode_utf8(field104, realloc, memory, caller)
        _store(ctypes.c_uint32, memory, caller, ptr, 164, len108)
        _store(ctypes.c_uint32, memory, caller, ptr, 160, ptr107)
        _store(ctypes.c_uint64, memory, caller, ptr, 168, _clamp(field105, -9223372036854775808, 9223372036854775807))
        _store(ctypes.c_float, memory, caller, ptr, 176, field106)
        ret = self._deeparg(caller, ptr)
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
