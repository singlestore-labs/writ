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

class Record(Protocol):
    @abstractmethod
    def construct_bar(self, name: str, age: int) -> Bar:
        raise NotImplementedError
    @abstractmethod
    def test_record(self, a: Bar) -> int:
        raise NotImplementedError
    @abstractmethod
    def test_deep_record(self, a: DeepBar) -> int:
        raise NotImplementedError
    @abstractmethod
    def test_deeper_record(self, a: DeeperBar) -> int:
        raise NotImplementedError
    @abstractmethod
    def bar(self, a: Bar) -> Bar:
        raise NotImplementedError
    @abstractmethod
    def deep_bar(self, a: Bar) -> DeepBar:
        raise NotImplementedError
    @abstractmethod
    def deeper_bar(self, a: Bar) -> DeeperBar:
        raise NotImplementedError
    @abstractmethod
    def rev_deeper_bar(self, a: DeeperBar) -> DeeperBar:
        raise NotImplementedError
    @abstractmethod
    def foo(self) -> Foo:
        raise NotImplementedError
    @abstractmethod
    def test_foo(self, a: Foo) -> Foo:
        raise NotImplementedError

def add_record_to_linker(linker: wasmtime.Linker, store: wasmtime.Store, host: Record) -> None:
    ty = wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32()], [])
    def construct_bar(caller: wasmtime.Caller, arg0: int, arg1: int, arg2: int, arg3: int) -> None:
        m = caller["memory"]
        assert(isinstance(m, wasmtime.Memory))
        memory = cast(wasmtime.Memory, m)
        realloc = caller["canonical_abi_realloc"]
        assert(isinstance(realloc, wasmtime.Func))
        ptr = arg0
        len0 = arg1
        ret = host.construct_bar(_decode_utf8(memory, caller, ptr, len0), arg2)
        record = ret
        field = record.name
        field1 = record.age
        ptr2, len3 = _encode_utf8(field, realloc, memory, caller)
        _store(ctypes.c_uint32, memory, caller, arg3, 4, len3)
        _store(ctypes.c_uint32, memory, caller, arg3, 0, ptr2)
        _store(ctypes.c_uint32, memory, caller, arg3, 8, _clamp(field1, -2147483648, 2147483647))
    linker.define('record', 'construct-bar', wasmtime.Func(store, ty, construct_bar, access_caller = True))
    ty = wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32()], [wasmtime.ValType.i32()])
    def test_record(caller: wasmtime.Caller, arg0: int, arg1: int, arg2: int) -> int:
        m = caller["memory"]
        assert(isinstance(m, wasmtime.Memory))
        memory = cast(wasmtime.Memory, m)
        ptr = arg0
        len0 = arg1
        ret = host.test_record(Bar(_decode_utf8(memory, caller, ptr, len0), arg2))
        return _clamp(ret, -2147483648, 2147483647)
    linker.define('record', 'test-record', wasmtime.Func(store, ty, test_record, access_caller = True))
    ty = wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32()], [wasmtime.ValType.i32()])
    def test_deep_record(caller: wasmtime.Caller, arg0: int, arg1: int, arg2: int, arg3: int) -> int:
        m = caller["memory"]
        assert(isinstance(m, wasmtime.Memory))
        memory = cast(wasmtime.Memory, m)
        ptr = arg1
        len0 = arg2
        ret = host.test_deep_record(DeepBar(arg0, Bar(_decode_utf8(memory, caller, ptr, len0), arg3)))
        return _clamp(ret, -2147483648, 2147483647)
    linker.define('record', 'test-deep-record', wasmtime.Func(store, ty, test_deep_record, access_caller = True))
    ty = wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32()], [wasmtime.ValType.i32()])
    def test_deeper_record(caller: wasmtime.Caller, arg0: int, arg1: int, arg2: int, arg3: int, arg4: int) -> int:
        m = caller["memory"]
        assert(isinstance(m, wasmtime.Memory))
        memory = cast(wasmtime.Memory, m)
        ptr = arg2
        len0 = arg3
        ret = host.test_deeper_record(DeeperBar(arg0, DeepBar(arg1, Bar(_decode_utf8(memory, caller, ptr, len0), arg4))))
        return _clamp(ret, -2147483648, 2147483647)
    linker.define('record', 'test-deeper-record', wasmtime.Func(store, ty, test_deeper_record, access_caller = True))
    ty = wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32()], [])
    def bar(caller: wasmtime.Caller, arg0: int, arg1: int, arg2: int, arg3: int) -> None:
        m = caller["memory"]
        assert(isinstance(m, wasmtime.Memory))
        memory = cast(wasmtime.Memory, m)
        realloc = caller["canonical_abi_realloc"]
        assert(isinstance(realloc, wasmtime.Func))
        ptr = arg0
        len0 = arg1
        ret = host.bar(Bar(_decode_utf8(memory, caller, ptr, len0), arg2))
        record = ret
        field = record.name
        field1 = record.age
        ptr2, len3 = _encode_utf8(field, realloc, memory, caller)
        _store(ctypes.c_uint32, memory, caller, arg3, 4, len3)
        _store(ctypes.c_uint32, memory, caller, arg3, 0, ptr2)
        _store(ctypes.c_uint32, memory, caller, arg3, 8, _clamp(field1, -2147483648, 2147483647))
    linker.define('record', 'bar', wasmtime.Func(store, ty, bar, access_caller = True))
    ty = wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32()], [])
    def deep_bar(caller: wasmtime.Caller, arg0: int, arg1: int, arg2: int, arg3: int) -> None:
        m = caller["memory"]
        assert(isinstance(m, wasmtime.Memory))
        memory = cast(wasmtime.Memory, m)
        realloc = caller["canonical_abi_realloc"]
        assert(isinstance(realloc, wasmtime.Func))
        ptr = arg0
        len0 = arg1
        ret = host.deep_bar(Bar(_decode_utf8(memory, caller, ptr, len0), arg2))
        record = ret
        field = record.id
        field1 = record.x
        _store(ctypes.c_uint32, memory, caller, arg3, 0, _clamp(field, -2147483648, 2147483647))
        record2 = field1
        field3 = record2.name
        field4 = record2.age
        ptr5, len6 = _encode_utf8(field3, realloc, memory, caller)
        _store(ctypes.c_uint32, memory, caller, arg3, 8, len6)
        _store(ctypes.c_uint32, memory, caller, arg3, 4, ptr5)
        _store(ctypes.c_uint32, memory, caller, arg3, 12, _clamp(field4, -2147483648, 2147483647))
    linker.define('record', 'deep-bar', wasmtime.Func(store, ty, deep_bar, access_caller = True))
    ty = wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32()], [])
    def deeper_bar(caller: wasmtime.Caller, arg0: int, arg1: int, arg2: int, arg3: int) -> None:
        m = caller["memory"]
        assert(isinstance(m, wasmtime.Memory))
        memory = cast(wasmtime.Memory, m)
        realloc = caller["canonical_abi_realloc"]
        assert(isinstance(realloc, wasmtime.Func))
        ptr = arg0
        len0 = arg1
        ret = host.deeper_bar(Bar(_decode_utf8(memory, caller, ptr, len0), arg2))
        record = ret
        field = record.id
        field1 = record.x
        _store(ctypes.c_uint32, memory, caller, arg3, 0, _clamp(field, -2147483648, 2147483647))
        record2 = field1
        field3 = record2.id
        field4 = record2.x
        _store(ctypes.c_uint32, memory, caller, arg3, 4, _clamp(field3, -2147483648, 2147483647))
        record5 = field4
        field6 = record5.name
        field7 = record5.age
        ptr8, len9 = _encode_utf8(field6, realloc, memory, caller)
        _store(ctypes.c_uint32, memory, caller, arg3, 12, len9)
        _store(ctypes.c_uint32, memory, caller, arg3, 8, ptr8)
        _store(ctypes.c_uint32, memory, caller, arg3, 16, _clamp(field7, -2147483648, 2147483647))
    linker.define('record', 'deeper-bar', wasmtime.Func(store, ty, deeper_bar, access_caller = True))
    ty = wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32()], [])
    def rev_deeper_bar(caller: wasmtime.Caller, arg0: int, arg1: int, arg2: int, arg3: int, arg4: int, arg5: int) -> None:
        m = caller["memory"]
        assert(isinstance(m, wasmtime.Memory))
        memory = cast(wasmtime.Memory, m)
        realloc = caller["canonical_abi_realloc"]
        assert(isinstance(realloc, wasmtime.Func))
        ptr = arg2
        len0 = arg3
        ret = host.rev_deeper_bar(DeeperBar(arg0, DeepBar(arg1, Bar(_decode_utf8(memory, caller, ptr, len0), arg4))))
        record = ret
        field = record.id
        field1 = record.x
        _store(ctypes.c_uint32, memory, caller, arg5, 0, _clamp(field, -2147483648, 2147483647))
        record2 = field1
        field3 = record2.id
        field4 = record2.x
        _store(ctypes.c_uint32, memory, caller, arg5, 4, _clamp(field3, -2147483648, 2147483647))
        record5 = field4
        field6 = record5.name
        field7 = record5.age
        ptr8, len9 = _encode_utf8(field6, realloc, memory, caller)
        _store(ctypes.c_uint32, memory, caller, arg5, 12, len9)
        _store(ctypes.c_uint32, memory, caller, arg5, 8, ptr8)
        _store(ctypes.c_uint32, memory, caller, arg5, 16, _clamp(field7, -2147483648, 2147483647))
    linker.define('record', 'rev-deeper-bar', wasmtime.Func(store, ty, rev_deeper_bar, access_caller = True))
    ty = wasmtime.FuncType([wasmtime.ValType.i32()], [])
    def foo(caller: wasmtime.Caller, arg0: int) -> None:
        m = caller["memory"]
        assert(isinstance(m, wasmtime.Memory))
        memory = cast(wasmtime.Memory, m)
        realloc = caller["canonical_abi_realloc"]
        assert(isinstance(realloc, wasmtime.Func))
        ret = host.foo()
        record = ret
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
        _store(ctypes.c_uint32, memory, caller, arg0, 4, len5)
        _store(ctypes.c_uint32, memory, caller, arg0, 0, result)
        ptr7, len8 = _list_canon_lower(field0, ctypes.c_int32, 4, 4, realloc, memory, caller)
        _store(ctypes.c_uint32, memory, caller, arg0, 12, len8)
        _store(ctypes.c_uint32, memory, caller, arg0, 8, ptr7)
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
        _store(ctypes.c_uint32, memory, caller, arg0, 20, len18)
        _store(ctypes.c_uint32, memory, caller, arg0, 16, result17)
        vec22 = field2
        len24 = len(vec22)
        result23 = realloc(caller, 0, 0, 1, len24 * 1)
        assert(isinstance(result23, int))
        for i25 in range(0, len24):
            e20 = vec22[i25]
            base21 = result23 + i25 * 1
            _store(ctypes.c_uint8, memory, caller, base21, 0, int(e20))
        _store(ctypes.c_uint32, memory, caller, arg0, 28, len24)
        _store(ctypes.c_uint32, memory, caller, arg0, 24, result23)
    linker.define('record', 'foo', wasmtime.Func(store, ty, foo, access_caller = True))
    ty = wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32()], [])
    def test_foo(caller: wasmtime.Caller, arg0: int, arg1: int, arg2: int, arg3: int, arg4: int, arg5: int, arg6: int, arg7: int, arg8: int) -> None:
        m = caller["memory"]
        assert(isinstance(m, wasmtime.Memory))
        memory = cast(wasmtime.Memory, m)
        realloc = caller["canonical_abi_realloc"]
        assert(isinstance(realloc, wasmtime.Func))
        ptr3 = arg0
        len4 = arg1
        result: List[str] = []
        for i5 in range(0, len4):
            base0 = ptr3 + i5 * 8
            load = _load(ctypes.c_int32, memory, caller, base0, 0)
            load1 = _load(ctypes.c_int32, memory, caller, base0, 4)
            ptr = load
            len2 = load1
            result.append(_decode_utf8(memory, caller, ptr, len2))
        ptr6 = arg2
        len7 = arg3
        ptr14 = arg4
        len15 = arg5
        result16: List[Bar] = []
        for i17 in range(0, len15):
            base8 = ptr14 + i17 * 12
            load9 = _load(ctypes.c_int32, memory, caller, base8, 0)
            load10 = _load(ctypes.c_int32, memory, caller, base8, 4)
            ptr11 = load9
            len12 = load10
            load13 = _load(ctypes.c_int32, memory, caller, base8, 8)
            result16.append(Bar(_decode_utf8(memory, caller, ptr11, len12), load13))
        ptr20 = arg6
        len21 = arg7
        result22: List[bool] = []
        for i23 in range(0, len21):
            base18 = ptr20 + i23 * 1
            load19 = _load(ctypes.c_uint8, memory, caller, base18, 0)
            
            operand = load19
            if operand == 0:
                boolean = False
            elif operand == 1:
                boolean = True
            else:
                raise TypeError("invalid variant discriminant for bool")
            result22.append(boolean)
        ret = host.test_foo(Foo(result, cast(List[int], _list_canon_lift(ptr6, len7, 4, ctypes.c_int32, memory, caller)), result16, result22))
        record = ret
        field = record.movies
        field24 = record.code
        field25 = record.bars
        field26 = record.b
        vec = field
        len31 = len(vec)
        result30 = realloc(caller, 0, 0, 4, len31 * 8)
        assert(isinstance(result30, int))
        for i32 in range(0, len31):
            e = vec[i32]
            base27 = result30 + i32 * 8
            ptr28, len29 = _encode_utf8(e, realloc, memory, caller)
            _store(ctypes.c_uint32, memory, caller, base27, 4, len29)
            _store(ctypes.c_uint32, memory, caller, base27, 0, ptr28)
        _store(ctypes.c_uint32, memory, caller, arg8, 4, len31)
        _store(ctypes.c_uint32, memory, caller, arg8, 0, result30)
        ptr33, len34 = _list_canon_lower(field24, ctypes.c_int32, 4, 4, realloc, memory, caller)
        _store(ctypes.c_uint32, memory, caller, arg8, 12, len34)
        _store(ctypes.c_uint32, memory, caller, arg8, 8, ptr33)
        vec42 = field25
        len44 = len(vec42)
        result43 = realloc(caller, 0, 0, 4, len44 * 12)
        assert(isinstance(result43, int))
        for i45 in range(0, len44):
            e35 = vec42[i45]
            base36 = result43 + i45 * 12
            record37 = e35
            field38 = record37.name
            field39 = record37.age
            ptr40, len41 = _encode_utf8(field38, realloc, memory, caller)
            _store(ctypes.c_uint32, memory, caller, base36, 4, len41)
            _store(ctypes.c_uint32, memory, caller, base36, 0, ptr40)
            _store(ctypes.c_uint32, memory, caller, base36, 8, _clamp(field39, -2147483648, 2147483647))
        _store(ctypes.c_uint32, memory, caller, arg8, 20, len44)
        _store(ctypes.c_uint32, memory, caller, arg8, 16, result43)
        vec48 = field26
        len50 = len(vec48)
        result49 = realloc(caller, 0, 0, 1, len50 * 1)
        assert(isinstance(result49, int))
        for i51 in range(0, len50):
            e46 = vec48[i51]
            base47 = result49 + i51 * 1
            _store(ctypes.c_uint8, memory, caller, base47, 0, int(e46))
        _store(ctypes.c_uint32, memory, caller, arg8, 28, len50)
        _store(ctypes.c_uint32, memory, caller, arg8, 24, result49)
    linker.define('record', 'test-foo', wasmtime.Func(store, ty, test_foo, access_caller = True))
