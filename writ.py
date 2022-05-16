import argparse
import collections
import error_handler
import importlib
import inspect
import json
import operator
import os
import parse_input
import parse_json
import re
import string
import subprocess
import sys
import typing
import wasmtime
from enum import Enum
from typing import Optional

binding_path = "binds/"


class ErrorCode(Enum):
    CONVERT_TO_JSON_FAIL = "fail to convert to json string"
    INVOKE_INITIALIZE_FAIL = "fail to invoke _initialize"
    MISSING_INPUT = (
        "either wasm file path or function name is missing from the input arguments"
    )
    OBJECT_NOT_FOUND = "no object found in target: "
    PATH_NOT_EXIST = "file path doesn't exist: "
    TYPE_NOT_IMPLEMENTED = "type not implemented: "
    UNKNOWN = "unknown error in writ, likely caused by wrong/missing arguments"


def to_json(pyobj: str) -> Optional[str]:
    if hasattr(pyobj, "__dict__"):
        return {k: to_json(v) for k, v in pyobj.__dict__.items()}
    elif isinstance(pyobj, list) or isinstance(pyobj, tuple):
        return [to_json(x) for x in pyobj]
    elif isinstance(pyobj, str):
        return pyobj
    elif isinstance(pyobj, int) or isinstance(pyobj, float):
        return pyobj
    elif isinstance(pyobj, bool):
        return pyobj.lower()
    else:
        return None


class Imports:
    wit_file_name: Optional[str]
    wasm_file: str
    func: str
    args: [str]
    classes: dict

    def __init__(self) -> None:
        (binding_path, wit_path, input_args) = parse_input.parse()
        if len(input_args) < 2:
            error_handler.return_error(ErrorCode.MISSING_INPUT.value)
        if binding_path[-1] != "/":
            binding_path += "/"

        self.wasm_file = input_args[0]
        self.func = input_args[1].replace("-", "_")
        self.args = [json.loads(x) for x in input_args[2:]]

        if wit_path is None:
            self.wit_file_name = None
        else:
            self.wit_file_name = re.findall(r"[^\/]+(?=\.)", wit_path)[-1]

            # generate bindings
            export_file_name = f"{self.wit_file_name}_export_bindings"
            import_file_name = f"{self.wit_file_name}_import_bindings"
            export_file_path = f"{binding_path}{export_file_name}.py"
            import_file_path = f"{binding_path}{import_file_name}.py"

            if not os.path.exists(export_file_path):
                os.system("wit-bindgen wasmtime-py --export " + wit_path)
                os.system(f"mv bindings.py {export_file_path}")

            if not os.path.exists(import_file_path):
                os.system("wit-bindgen wasmtime-py --import " + wit_path)
                os.system(f"mv bindings.py {import_file_path}")

            sys.path.insert(1, binding_path)
            self.imported = importlib.import_module(import_file_name)
            self.exported = importlib.import_module(export_file_name)

    def get_types(self, class_name: str) -> list[typing.types]:
        py_import_classes = inspect.getmembers(
            self.imported,
            lambda x: inspect.isclass(x) and x.__name__ == class_name,
        )
        py_import_class = error_handler.assert_and_return(
            not py_import_classes,
            ErrorCode.OBJECT_NOT_FOUND.value + "class " + class_name,
            py_import_classes[0][1],
        )
        py_funcs = inspect.getmembers(
            py_import_class,
            lambda x: inspect.isfunction(x) and x.__name__ == self.func,
        )
        py_func = error_handler.assert_and_return(
            not py_funcs,
            ErrorCode.OBJECT_NOT_FOUND.value + "function " + self.func,
            py_funcs[0][1],
        )

        signatures = inspect.signature(py_func)
        return list(
            map(
                lambda x: signatures.parameters[x].annotation,
                signatures.parameters.keys(),
            )
        )

    def run_without_wit_arg(self) -> Optional[str]:
        command = ["wasmtime", "run", "--invoke", self.func, self.wasm_file] + [
            str(x) for x in self.args
        ]
        #  print("command: ", command)
        try:
            result = subprocess.run(command, capture_output=True)
            return result.stdout.decode("utf-8")
        except:
            return None  # error handling here

    def run_with_wit_arg(
        self, linker: wasmtime.Linker, store: wasmtime.Store, module: wasmtime.Module
    ) -> Optional[str]:
        linker_func_name = "add_" + self.wit_file_name + "_to_linker"
        eval("self.exported." + linker_func_name + "(linker, store, self)")

        # process arguments
        py_class_name = "".join(x.capitalize() for x in self.wit_file_name.split("_"))
        type_list = self.get_types(py_class_name)

        # evaluate
        ccommand = "self.imported." + py_class_name + "(store, linker, module)"
        wasm = eval(ccommand)

        classes = dict(inspect.getmembers(self.imported, inspect.isclass))
        parse_args_helper = parse_json.ParseJson(classes, self.imported)
        command = (
            "wasm."
            + self.func
            + "(store,"
            + parse_args_helper.parse_json_args(list(zip(self.args, type_list[2:])))
            + ")"
        )

        try:
            result = eval(command)
        except:
            result = None
        return result


def run() -> Optional[str]:
    # initialize
    imports = Imports()

    store = wasmtime.Store()
    module = wasmtime.Module.from_file(store.engine, imports.wasm_file)

    linker = wasmtime.Linker(store.engine)
    linker.define_wasi()
    linker.define_module(store, "test", module)

    wasi = wasmtime.WasiConfig()
    wasi.inherit_stdout()
    wasi.inherit_stderr()
    store.set_wasi(wasi)

    # invoke _initialize export
    #  try:
    #  maybe_func = linker.get(store, "test", "_initialize")
    #  maybe_func(store)
    #  except:
    #  print(ErrorCode.INVOKE_INITIALIZE_FAIL.value, file=sys.stderr)

    if imports.wit_file_name == None:
        result = imports.run_without_wit_arg()
    else:
        result = imports.run_with_wit_arg(linker, store, module)
    return result


if __name__ == "__main__":
    result = run()
    if result is None:
        print(ErrorCode.UNKNOWN.value, file=sys.stderr)
    else:
        json_result = json.dumps(to_json(result))
        if json_result is None:
            print(ErrorCode.CONVERT_TO_JSON_FAIL.value, file=sys.stderr)
        else:
            print(json_result)
