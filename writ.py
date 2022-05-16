import collections
import importlib
import inspect
import json
import operator
import os
import parse_json
import re
import string
import subprocess
import sys
import typing
import wasmtime
import error_handler
from enum import Enum
from typing import Optional

binding_path = "binds/"


class ErrorCode(Enum):
    CONVERT_TO_JSON_FAIL = "fail to convert to json string"
    INVOKE_INITIALIZE_FAIL = "fail to invoke _initialize"
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

    def __init__(self, cmd_args: list[str]) -> None:
        if cmd_args[1] == "--wit":
            wit_path = cmd_args[2]
            self.wit_file_name = re.findall(r"[^\/]+(?=\.)", wit_path)[-1]

            # generate bindings
            export_file_name = "{}_export_bindings".format(self.wit_file_name)
            import_file_name = "{}_import_bindings".format(self.wit_file_name)
            export_file_path = "{}{}.py".format(binding_path, export_file_name)
            import_file_path = "{}{}.py".format(binding_path, import_file_name)

            if not os.path.exists(export_file_path):
                error_handler.assert_and_run_command(
                    not os.path.exists(wit_path),
                    ErrorCode.PATH_NOT_EXIST.value + wit_path,
                    "wit-bindgen wasmtime-py --export " + wit_path,
                )
                os.system("mv bindings.py {}".format(export_file_path))

            if not os.path.exists(import_file_path):
                error_handler.assert_and_run_command(
                    not os.path.exists(wit_path),
                    ErrorCode.PATH_NOT_EXIST.value + wit_path,
                    "wit-bindgen wasmtime-py --import " + wit_path,
                )
                os.system("mv bindings.py {}".format(import_file_path))

            self.imported = importlib.import_module(
                import_file_path.replace("/", ".")[:-3]
            )
            self.exported = importlib.import_module(
                export_file_path.replace("/", ".")[:-3]
            )

            # parse the rest
            self.wasm_file = cmd_args[3]
            self.func = cmd_args[4].replace("-", "_")
            self.args = cmd_args[5:]
        else:  # need to validate the file path
            self.wit_file_name = None
            self.wasm_file = cmd_args[1]
            self.func = cmd_args[2]
            self.args = cmd_args[3:]

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
        #  print("py_class_name: ", py_class_name)
        #  print("type_list: ", type_list)

        # evaluate
        ccommand = "self.imported." + py_class_name + "(store, linker, module)"
        #  print(ccommand)
        wasm = eval(ccommand)
        #  print("LOAD JSON: " + "\n".join([str(json.loads(x)) for x in self.args]))

        classes = dict(inspect.getmembers(self.imported, inspect.isclass))
        parse_args_helper = parse_json.ParseJson(classes, self.imported)
        command = (
            "wasm."
            + self.func
            + "(store,"
            + parse_args_helper.parse_json_args(
                list(zip(list(map(json.loads, self.args)), type_list[2:]))
            )
            + ")"
        )

        print("command: ", command)

        try:
            result = eval(command)
        except:
            result = None
        return result


def run(cmd_args: list[str]) -> Optional[str]:
    # initialize
    imports = Imports(cmd_args)

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
    result = run(sys.argv)
    if result is None:
        print(ErrorCode.UNKNOWN.value, file=sys.stderr)
    else:
        print("FINAL RESULT: {}".format(result))
        json_result = json.dumps(to_json(result))
        if json_result is None:
            print(ErrorCode.CONVERT_TO_JSON_FAIL.value, file=sys.stderr)
        else:
            print("FINAL RESULT IN JSON FORMAT:")
            print(json_result)
