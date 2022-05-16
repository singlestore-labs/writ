import error_handler
import sys
import typing
from enum import Enum


class ErrorCode(Enum):
    ARG_TYPE_NOT_IMPLEMENTED = "arg type not implemented: "
    UNKNOWN = "unknown error in parse_json"
    TYPE_TO_STRING_NOT_IMPLEMENTED = "to json string not implemented: "
    TYPE_MISMATCH = "type mismatch between type of arg_value and arg_type: "


def is_atomic_type(arg: typing.Any):
    return (
        isinstance(arg, int)
        or isinstance(arg, float)
        or isinstance(arg, str)
        or isinstance(arg, bool)
    )


# convert to string, atomic type only
def to_string_arg(arg: typing.Any) -> str:
    if isinstance(arg, int) or isinstance(arg, float):
        return str(arg)
    elif isinstance(arg, str):
        return '"' + arg + '"'
    elif isinstance(arg, bool):
        return string.capwords(arg)
    else:
        error_handler.return_error(
            ErrorCode.TYPE_TO_STRING_NOT_IMPLEMENTED.value + str(type(arg))
        )


class ParseJson:
    classes: dict

    def __init__(self, classes, imported) -> None:
        self.classes = classes
        self.imported = imported

    # convert class (presented by a json dictionary) to string
    def process_dict_arg(self, arg_value: dict, arg_type: typing.types) -> str:
        class_name = arg_type.__name__
        class_obj = self.classes[class_name]
        class_types = list(class_obj.__annotations__.values())
        #  print(
        #  "class_name, class_obj, class_type, values: ",
        #  class_name,
        #  class_obj,
        #  class_types,
        #  arg_value.values(),
        #  )
        #  print("CLASS_TYPES: {}".format(class_types))
        command = (
            "self.imported."
            + class_name
            + "("
            + ",".join(
                map(
                    lambda x: self.process_arg(x),
                    zip(list(arg_value.values()), class_types),
                )
            )
            + ")"
        )
        return command

    def process_arg(self, arg: (typing.Any, typing.types)) -> str:
        arg_value, arg_type = arg[0], arg[1]
        print(
            "arg_value, arg_type, arg_value_type = {}, {}, {}".format(
                arg_value, arg_type, type(arg_value)
            )
        )
        # TODO: split checking if arg_value type match with arg_type for better debugging
        if is_atomic_type(arg_value):
            if type(arg_value) is not arg_type:
                error_handler.return_error(
                    ErrorCode.TYPE_MISMATCH
                    + "{} and {}".format(type(arg_value), arg_type)
                )
            return to_string_arg(arg_value)
        elif arg_type is bytes:
            # if arg type is bytes, arg value type is assumed to be in form of
            # array of integer [a_1, a_2, ..., a_n], a_i represent each bit i-th
            return str(b"".join([x.to_bytes(1, "big") for x in arg_value]))
        elif isinstance(arg_value, dict):
            return self.process_dict_arg(arg_value, arg_type)
        elif isinstance(arg_value, list):
            arg_elem_type = arg_type.__args__[0]  # type of each element in the list
            return (
                "["
                + ",".join([self.process_arg((x, arg_elem_type)) for x in arg_value])
                + "]"
            )
        else:
            error_handler.return_error(
                ErrorCode.ARG_TYPE_NOT_IMPLEMENTED.value + str(type(arg_value))
            )

    def parse_json_args(self, args: list[(str, typing.types)]) -> str:
        print("MY ARGS: " + str(args))
        result = ",".join(map(lambda x: self.process_arg(x), args))
        print("RESULT IS " + result)
        return result
