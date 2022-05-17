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
class Bar:
    name: str
    age: int

@dataclass
class DeepBar:
    id: int
    x: Bar

@dataclass
class DeeperBar:
    id: int
    x: DeepBar

@dataclass
class Foo:
    movies: List[str]
    code: List[int]
    bars: List[Bar]
    b: List[bool]

class Record:
    instance: wasmtime.Instance
    _bar: wasmtime.Func
    _canonical_abi_free: wasmtime.Func
    _canonical_abi_realloc: wasmtime.Func
    _construct_bar: wasmtime.Func
    _deep_bar: wasmtime.Func
    _deeper_bar: wasmtime.Func
    _foo: wasmtime.Func
    _memory: wasmtime.Memory
    _rev_deeper_bar: wasmtime.Func
    _test_deep_record: wasmtime.Func
    _test_deeper_record: wasmtime.Func
    _test_foo: wasmtime.Func
    _test_record: wasmtime.Func
    def __init__(self, store: wasmtime.Store, linker: wasmtime.Linker, module: wasmtime.Module):
        self.instance = linker.instantiate(store, module)
        exports = self.instance.exports(store)
        
        bar = exports['bar']
        assert(isinstance(bar, wasmtime.Func))
        self._bar = bar
        
        canonical_abi_free = exports['canonical_abi_free']
        assert(isinstance(canonical_abi_free, wasmtime.Func))
        self._canonical_abi_free = canonical_abi_free
        
        canonical_abi_realloc = exports['canonical_abi_realloc']
        assert(isinstance(canonical_abi_realloc, wasmtime.Func))
        self._canonical_abi_realloc = canonical_abi_realloc
        
        construct_bar = exports['construct-bar']
        assert(isinstance(construct_bar, wasmtime.Func))
        self._construct_bar = construct_bar
        
        deep_bar = exports['deep-bar']
        assert(isinstance(deep_bar, wasmtime.Func))
        self._deep_bar = deep_bar
        
        deeper_bar = exports['deeper-bar']
        assert(isinstance(deeper_bar, wasmtime.Func))
        self._deeper_bar = deeper_bar
        
        foo = exports['foo']
        assert(isinstance(foo, wasmtime.Func))
        self._foo = foo
        
        memory = exports['memory']
        assert(isinstance(memory, wasmtime.Memory))
        self._memory = memory
        
        rev_deeper_bar = exports['rev-deeper-bar']
        assert(isinstance(rev_deeper_bar, wasmtime.Func))
        self._rev_deeper_bar = rev_deeper_bar
        
        test_deep_record = exports['test-deep-record']
        assert(isinstance(test_deep_record, wasmtime.Func))
        self._test_deep_record = test_deep_record
        
        test_deeper_record = exports['test-deeper-record']
        assert(isinstance(test_deeper_record, wasmtime.Func))
        self._test_deeper_record = test_deeper_record
        
        test_foo = exports['test-foo']
        assert(isinstance(test_foo, wasmtime.Func))
        self._test_foo = test_foo
        
        test_record = exports['test-record']
        assert(isinstance(test_record, wasmtime.Func))
        self._test_record = test_record
    def construct_bar(self, caller: wasmtime.Store, name: str, age: int) -> Bar:
        memory = self._memory;
        realloc = self._canonical_abi_realloc
        free = self._canonical_abi_free
        ptr, len0 = _encode_utf8(name, realloc, memory, caller)
        ret = self._construct_bar(caller, ptr, len0, _clamp(age, -2147483648, 2147483647))
        assert(isinstance(ret, int))
        load = _load(ctypes.c_int32, memory, caller, ret, 0)
        load1 = _load(ctypes.c_int32, memory, caller, ret, 4)
        ptr2 = load
        len3 = load1
        list = _decode_utf8(memory, caller, ptr2, len3)
        free(caller, ptr2, len3, 1)
        load4 = _load(ctypes.c_int32, memory, caller, ret, 8)
        return Bar(list, load4)
    def test_record(self, caller: wasmtime.Store, a: Bar) -> int:
        memory = self._memory;
        realloc = self._canonical_abi_realloc
        record = a
        field = record.name
        field0 = record.age
        ptr, len1 = _encode_utf8(field, realloc, memory, caller)
        ret = self._test_record(caller, ptr, len1, _clamp(field0, -2147483648, 2147483647))
        assert(isinstance(ret, int))
        return ret
    def test_deep_record(self, caller: wasmtime.Store, a: DeepBar) -> int:
        memory = self._memory;
        realloc = self._canonical_abi_realloc
        record = a
        field = record.id
        field0 = record.x
        record1 = field0
        field2 = record1.name
        field3 = record1.age
        ptr, len4 = _encode_utf8(field2, realloc, memory, caller)
        ret = self._test_deep_record(caller, _clamp(field, -2147483648, 2147483647), ptr, len4, _clamp(field3, -2147483648, 2147483647))
        assert(isinstance(ret, int))
        return ret
    def test_deeper_record(self, caller: wasmtime.Store, a: DeeperBar) -> int:
        memory = self._memory;
        realloc = self._canonical_abi_realloc
        record = a
        field = record.id
        field0 = record.x
        record1 = field0
        field2 = record1.id
        field3 = record1.x
        record4 = field3
        field5 = record4.name
        field6 = record4.age
        ptr, len7 = _encode_utf8(field5, realloc, memory, caller)
        ret = self._test_deeper_record(caller, _clamp(field, -2147483648, 2147483647), _clamp(field2, -2147483648, 2147483647), ptr, len7, _clamp(field6, -2147483648, 2147483647))
        assert(isinstance(ret, int))
        return ret
    def bar(self, caller: wasmtime.Store, a: Bar) -> Bar:
        memory = self._memory;
        realloc = self._canonical_abi_realloc
        free = self._canonical_abi_free
        record = a
        field = record.name
        field0 = record.age
        ptr, len1 = _encode_utf8(field, realloc, memory, caller)
        ret = self._bar(caller, ptr, len1, _clamp(field0, -2147483648, 2147483647))
        assert(isinstance(ret, int))
        load = _load(ctypes.c_int32, memory, caller, ret, 0)
        load2 = _load(ctypes.c_int32, memory, caller, ret, 4)
        ptr3 = load
        len4 = load2
        list = _decode_utf8(memory, caller, ptr3, len4)
        free(caller, ptr3, len4, 1)
        load5 = _load(ctypes.c_int32, memory, caller, ret, 8)
        return Bar(list, load5)
    def deep_bar(self, caller: wasmtime.Store, a: Bar) -> DeepBar:
        memory = self._memory;
        realloc = self._canonical_abi_realloc
        free = self._canonical_abi_free
        record = a
        field = record.name
        field0 = record.age
        ptr, len1 = _encode_utf8(field, realloc, memory, caller)
        ret = self._deep_bar(caller, ptr, len1, _clamp(field0, -2147483648, 2147483647))
        assert(isinstance(ret, int))
        load = _load(ctypes.c_int32, memory, caller, ret, 0)
        load2 = _load(ctypes.c_int32, memory, caller, ret, 4)
        load3 = _load(ctypes.c_int32, memory, caller, ret, 8)
        ptr4 = load2
        len5 = load3
        list = _decode_utf8(memory, caller, ptr4, len5)
        free(caller, ptr4, len5, 1)
        load6 = _load(ctypes.c_int32, memory, caller, ret, 12)
        return DeepBar(load, Bar(list, load6))
    def deeper_bar(self, caller: wasmtime.Store, a: Bar) -> DeeperBar:
        memory = self._memory;
        realloc = self._canonical_abi_realloc
        free = self._canonical_abi_free
        record = a
        field = record.name
        field0 = record.age
        ptr, len1 = _encode_utf8(field, realloc, memory, caller)
        ret = self._deeper_bar(caller, ptr, len1, _clamp(field0, -2147483648, 2147483647))
        assert(isinstance(ret, int))
        load = _load(ctypes.c_int32, memory, caller, ret, 0)
        load2 = _load(ctypes.c_int32, memory, caller, ret, 4)
        load3 = _load(ctypes.c_int32, memory, caller, ret, 8)
        load4 = _load(ctypes.c_int32, memory, caller, ret, 12)
        ptr5 = load3
        len6 = load4
        list = _decode_utf8(memory, caller, ptr5, len6)
        free(caller, ptr5, len6, 1)
        load7 = _load(ctypes.c_int32, memory, caller, ret, 16)
        return DeeperBar(load, DeepBar(load2, Bar(list, load7)))
    def rev_deeper_bar(self, caller: wasmtime.Store, a: DeeperBar) -> DeeperBar:
        memory = self._memory;
        realloc = self._canonical_abi_realloc
        free = self._canonical_abi_free
        record = a
        field = record.id
        field0 = record.x
        record1 = field0
        field2 = record1.id
        field3 = record1.x
        record4 = field3
        field5 = record4.name
        field6 = record4.age
        ptr, len7 = _encode_utf8(field5, realloc, memory, caller)
        ret = self._rev_deeper_bar(caller, _clamp(field, -2147483648, 2147483647), _clamp(field2, -2147483648, 2147483647), ptr, len7, _clamp(field6, -2147483648, 2147483647))
        assert(isinstance(ret, int))
        load = _load(ctypes.c_int32, memory, caller, ret, 0)
        load8 = _load(ctypes.c_int32, memory, caller, ret, 4)
        load9 = _load(ctypes.c_int32, memory, caller, ret, 8)
        load10 = _load(ctypes.c_int32, memory, caller, ret, 12)
        ptr11 = load9
        len12 = load10
        list = _decode_utf8(memory, caller, ptr11, len12)
        free(caller, ptr11, len12, 1)
        load13 = _load(ctypes.c_int32, memory, caller, ret, 16)
        return DeeperBar(load, DeepBar(load8, Bar(list, load13)))
    def foo(self, caller: wasmtime.Store) -> Foo:
        memory = self._memory;
        free = self._canonical_abi_free
        ret = self._foo(caller)
        assert(isinstance(ret, int))
        load = _load(ctypes.c_int32, memory, caller, ret, 0)
        load0 = _load(ctypes.c_int32, memory, caller, ret, 4)
        ptr5 = load
        len6 = load0
        result: List[str] = []
        for i7 in range(0, len6):
            base1 = ptr5 + i7 * 8
            load2 = _load(ctypes.c_int32, memory, caller, base1, 0)
            load3 = _load(ctypes.c_int32, memory, caller, base1, 4)
            ptr = load2
            len4 = load3
            list = _decode_utf8(memory, caller, ptr, len4)
            free(caller, ptr, len4, 1)
            result.append(list)
        free(caller, ptr5, len6 * 8, 4)
        load8 = _load(ctypes.c_int32, memory, caller, ret, 8)
        load9 = _load(ctypes.c_int32, memory, caller, ret, 12)
        ptr10 = load8
        len11 = load9
        list12 = cast(List[int], _list_canon_lift(ptr10, len11, 4, ctypes.c_int32, memory, caller))
        free(caller, ptr10, len11, 4)
        load13 = _load(ctypes.c_int32, memory, caller, ret, 16)
        load14 = _load(ctypes.c_int32, memory, caller, ret, 20)
        ptr22 = load13
        len23 = load14
        result24: List[Bar] = []
        for i25 in range(0, len23):
            base15 = ptr22 + i25 * 12
            load16 = _load(ctypes.c_int32, memory, caller, base15, 0)
            load17 = _load(ctypes.c_int32, memory, caller, base15, 4)
            ptr18 = load16
            len19 = load17
            list20 = _decode_utf8(memory, caller, ptr18, len19)
            free(caller, ptr18, len19, 1)
            load21 = _load(ctypes.c_int32, memory, caller, base15, 8)
            result24.append(Bar(list20, load21))
        free(caller, ptr22, len23 * 12, 4)
        load26 = _load(ctypes.c_int32, memory, caller, ret, 24)
        load27 = _load(ctypes.c_int32, memory, caller, ret, 28)
        ptr30 = load26
        len31 = load27
        result32: List[bool] = []
        for i33 in range(0, len31):
            base28 = ptr30 + i33 * 1
            load29 = _load(ctypes.c_uint8, memory, caller, base28, 0)
            
            operand = load29
            if operand == 0:
                boolean = False
            elif operand == 1:
                boolean = True
            else:
                raise TypeError("invalid variant discriminant for bool")
            result32.append(boolean)
        free(caller, ptr30, len31 * 1, 1)
        return Foo(result, list12, result24, result32)
    def test_foo(self, caller: wasmtime.Store, a: Foo) -> Foo:
        memory = self._memory;
        realloc = self._canonical_abi_realloc
        free = self._canonical_abi_free
        record = a
        field = record.movies
        field0 = record.code
        field1 = record.bars
        field2 = record.b
        vec = field
        len5 = len(vec)
        result = realloc(caller, 0, 0, 4, len5 * 8)
        assert(isinstance(result, int))
        for i6 in range(0, len5):
            e = vec[i6]
            base3 = result + i6 * 8
            ptr, len4 = _encode_utf8(e, realloc, memory, caller)
            _store(ctypes.c_uint32, memory, caller, base3, 4, len4)
            _store(ctypes.c_uint32, memory, caller, base3, 0, ptr)
        ptr7, len8 = _list_canon_lower(field0, ctypes.c_int32, 4, 4, realloc, memory, caller)
        vec16 = field1
        len18 = len(vec16)
        result17 = realloc(caller, 0, 0, 4, len18 * 12)
        assert(isinstance(result17, int))
        for i19 in range(0, len18):
            e9 = vec16[i19]
            base10 = result17 + i19 * 12
            record11 = e9
            field12 = record11.name
            field13 = record11.age
            ptr14, len15 = _encode_utf8(field12, realloc, memory, caller)
            _store(ctypes.c_uint32, memory, caller, base10, 4, len15)
            _store(ctypes.c_uint32, memory, caller, base10, 0, ptr14)
            _store(ctypes.c_uint32, memory, caller, base10, 8, _clamp(field13, -2147483648, 2147483647))
        vec22 = field2
        len24 = len(vec22)
        result23 = realloc(caller, 0, 0, 1, len24 * 1)
        assert(isinstance(result23, int))
        for i25 in range(0, len24):
            e20 = vec22[i25]
            base21 = result23 + i25 * 1
            _store(ctypes.c_uint8, memory, caller, base21, 0, int(e20))
        ret = self._test_foo(caller, result, len5, ptr7, len8, result17, len18, result23, len24)
        assert(isinstance(ret, int))
        load = _load(ctypes.c_int32, memory, caller, ret, 0)
        load26 = _load(ctypes.c_int32, memory, caller, ret, 4)
        ptr32 = load
        len33 = load26
        result34: List[str] = []
        for i35 in range(0, len33):
            base27 = ptr32 + i35 * 8
            load28 = _load(ctypes.c_int32, memory, caller, base27, 0)
            load29 = _load(ctypes.c_int32, memory, caller, base27, 4)
            ptr30 = load28
            len31 = load29
            list = _decode_utf8(memory, caller, ptr30, len31)
            free(caller, ptr30, len31, 1)
            result34.append(list)
        free(caller, ptr32, len33 * 8, 4)
        load36 = _load(ctypes.c_int32, memory, caller, ret, 8)
        load37 = _load(ctypes.c_int32, memory, caller, ret, 12)
        ptr38 = load36
        len39 = load37
        list40 = cast(List[int], _list_canon_lift(ptr38, len39, 4, ctypes.c_int32, memory, caller))
        free(caller, ptr38, len39, 4)
        load41 = _load(ctypes.c_int32, memory, caller, ret, 16)
        load42 = _load(ctypes.c_int32, memory, caller, ret, 20)
        ptr50 = load41
        len51 = load42
        result52: List[Bar] = []
        for i53 in range(0, len51):
            base43 = ptr50 + i53 * 12
            load44 = _load(ctypes.c_int32, memory, caller, base43, 0)
            load45 = _load(ctypes.c_int32, memory, caller, base43, 4)
            ptr46 = load44
            len47 = load45
            list48 = _decode_utf8(memory, caller, ptr46, len47)
            free(caller, ptr46, len47, 1)
            load49 = _load(ctypes.c_int32, memory, caller, base43, 8)
            result52.append(Bar(list48, load49))
        free(caller, ptr50, len51 * 12, 4)
        load54 = _load(ctypes.c_int32, memory, caller, ret, 24)
        load55 = _load(ctypes.c_int32, memory, caller, ret, 28)
        ptr58 = load54
        len59 = load55
        result60: List[bool] = []
        for i61 in range(0, len59):
            base56 = ptr58 + i61 * 1
            load57 = _load(ctypes.c_uint8, memory, caller, base56, 0)
            
            operand = load57
            if operand == 0:
                boolean = False
            elif operand == 1:
                boolean = True
            else:
                raise TypeError("invalid variant discriminant for bool")
            result60.append(boolean)
        free(caller, ptr58, len59 * 1, 1)
        return Foo(result34, list40, result52, result60)
