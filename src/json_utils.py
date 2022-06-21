import error_handler
import json
import sys
import typing


def check_and_load(json_args: str, index: int) -> str:
    try:
        loaded_json = json.loads(json_args[index])
    except:
        print(
            f"ERROR: Failed to load json object at index {str(index - 1)}. Check your json syntax again.",
            file=sys.stderr,
        )
        sys.exit(1)
    return loaded_json


def to_py_obj(pyobj: str) -> typing.Any:
    if hasattr(pyobj, "__dict__"):
        return {k: to_py_obj(v) for k, v in pyobj.__dict__.items()}
    elif isinstance(pyobj, list) or isinstance(pyobj, tuple):
        return [to_py_obj(x) for x in pyobj]
    elif isinstance(pyobj, str):
        return pyobj
    elif isinstance(pyobj, int) or isinstance(pyobj, float):
        return pyobj
    elif isinstance(pyobj, bool):
        return pyobj.lower()
    raise error_handler.Error(
        error_handler.ErrorCode.PYOBJ_TO_PYSTR_FAILED,
        f"ERROR: Convert following Python type: {type(pyobj)} to Python str is not implemented",
    )
    sys.exit(1)


def is_atomic_type(arg: typing.Any) -> bool:
    return (
        isinstance(arg, int)
        or isinstance(arg, float)
        or isinstance(arg, str)
        or isinstance(arg, bool)
    )


class ParseJson:
    classes: dict

    def __init__(self, classes, imported) -> None:
        self.classes = classes
        self.imported = imported

    # convert class (presented by a json dictionary) to string
    def process_dict_arg(self, arg_value: dict, arg_type: type) -> str:
        class_name = arg_type.__name__
        class_obj = self.classes[class_name]
        class_types = list(class_obj.__annotations__.values())
        class_args = [
            self.process_arg(x) for x in zip(list(arg_value.values()), class_types)
        ]
        return getattr(self.imported, class_name)(*class_args)

    def process_arg(self, arg: tuple[typing.Any, typing.Any]) -> typing.Any:
        arg_value, arg_type = arg[0], arg[1]
        if is_atomic_type(arg_value):
            if type(arg_value) is not arg_type:
                print(
                    f"ERROR: Type mismatch between {arg_value} and {arg_type}. Check your input again.",
                    file=sys.stderr,
                )
                sys.exit(1)
            return arg_value
        elif arg_type is bytes:
            # if arg type is bytes, arg value type is assumed to be in form of
            # array of integer [a_1, a_2, ..., a_n], a_i represent each bit i-th
            return b"".join([x.to_bytes(1, "big") for x in arg_value])
        elif isinstance(arg_value, dict):
            return self.process_dict_arg(arg_value, arg_type)
        elif isinstance(arg_value, list):
            arg_elem_type = arg_type.__args__[0]  # type of each element in the list
            return [self.process_arg((x, arg_elem_type)) for x in arg_value]
        else:
            raise error_handler.Error(
                error_handler.ErrorCode.ARG_TYPE_NOT_IMPLEMENTED,
                f"Parsing json for the type: {str(type(arg_value))} is not implemented.",
            )

    def parse_json_args(self, args: list[tuple[typing.Any, type]]) -> list[typing.Any]:
        return [self.process_arg(x) for x in args]
