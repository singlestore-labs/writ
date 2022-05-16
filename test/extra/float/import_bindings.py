from abc import abstractmethod
from typing import Any
import wasmtime

try:
    from typing import Protocol
except ImportError:
    class Protocol: # type: ignore
        pass

class Power:
    instance: wasmtime.Instance
    _power_of: wasmtime.Func
    def __init__(self, store: wasmtime.Store, linker: wasmtime.Linker, module: wasmtime.Module):
        self.instance = linker.instantiate(store, module)
        exports = self.instance.exports(store)
        
        power_of = exports['power-of']
        assert(isinstance(power_of, wasmtime.Func))
        self._power_of = power_of
    def power_of(self, caller: wasmtime.Store, a: float, b: float) -> float:
        ret = self._power_of(caller, a, b)
        assert(isinstance(ret, float))
        return ret
