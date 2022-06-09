"""
validate path, user input, etc
"""
import error_handler
import filecmp
import os
import shutil
import typing
import validate

from enum import Enum


class ErrorCode(Enum):
    EMPTY_STRING = "Empty string or string not found."
    VARIABLE_DOES_NOT_EXIST = "Missing the following variable in PATH: "
    PATH_NOT_EXECUTABLE = "The following path is not executable: "


def resolve_string(s: typing.Optional[str]) -> str:
    if s is None:
        error_handler.return_error(ErrorCode.EMPTY_STRING.value)
    return str(s)


def check_command(env_name: str, command: str) -> typing.Optional[str]:
    ENV_CMD = os.environ.get(env_name)
    if ENV_CMD is not None:
        return ENV_CMD
    path = shutil.which(command)
    if path is None:
        error_handler.return_error(ErrorCode.VARIABLE_DOES_NOT_EXIST.value)
    if not os.access(os.path.abspath(validate.resolve_string(path)), os.X_OK):
        error_handler.return_error(ErrorCode.PATH_NOT_EXECUTABLE.value)
    return path


def generate_and_move(gen_cmd, file_path):
    os.system(gen_cmd)
    shutil.move("bindings.py", file_path)


def check_cached_file_or_generate(
    WIT_BINDGEN_PATH: typing.Optional[str],
    wit_path: str,
    cached_wit_path: str,
    export_path,
    import_path,
) -> None:
    if not os.path.exists(cached_wit_path) or not filecmp.cmp(
        cached_wit_path, wit_path, shallow=False
    ):
        generate_and_move(
            f"{validate.resolve_string(WIT_BINDGEN_PATH)} wasmtime-py --export {wit_path}",
            export_path,
        )
        generate_and_move(
            f"{validate.resolve_string(WIT_BINDGEN_PATH)} wasmtime-py --import {wit_path}",
            import_path,
        )
        shutil.copyfile(wit_path, cached_wit_path)
