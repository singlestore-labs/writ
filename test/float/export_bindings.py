from abc import abstractmethod
from typing import Any
import wasmtime

try:
    from typing import Protocol
except ImportError:
    class Protocol: # type: ignore
        pass

class Power(Protocol):
    @abstractmethod
    def power_of(self, a: float, b: float) -> float:
        raise NotImplementedError

def add_power_to_linker(linker: wasmtime.Linker, store: wasmtime.Store, host: Power) -> None:
    ty = wasmtime.FuncType([wasmtime.ValType.f32(), wasmtime.ValType.f32()], [wasmtime.ValType.f32()])
    def power_of(caller: wasmtime.Caller, arg0: float, arg1: float) -> float:
        ret = host.power_of(arg0, arg1)
        return ret
    linker.define('power', 'power-of', wasmtime.Func(store, ty, power_of, access_caller = True))
