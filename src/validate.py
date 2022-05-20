"""
validate path, user input, etc
"""
import error_handler
import filecmp
import os
import shutil

from enum import Enum


class ErrorCode(Enum):
    VARIABLE_DOES_NOT_EXIST = "Missing the following variable in PATH: "
    PATH_NOT_EXECUTABLE = "The following path is not executable: "


def check_command(command: str) -> str:
    path = shutil.which(command)
    if path is None:
        error_handler.return_error(COMMAND_DOES_NOT_EXIST.value)
    if not os.access(path, os.X_OK):
        error_handler.return_error(PATH_NOT_EXECUTABLE.value)
    return path


def generate_and_move(gen_cmd, file_path):
    os.system(gen_cmd)
    shutil.move("bindings.py", file_path)


def check_cached_file_or_generate(
    WIT_BINDGEN_PATH: str,
    wit_path: str,
    cached_wit_path: str,
    export_path,
    import_path,
) -> None:
    if not os.path.exists(cached_wit_path) or not filecmp.cmp(
        cached_wit_path, wit_path, shallow=False
    ):
        generate_and_move(
            f"{WIT_BINDGEN_PATH} wasmtime-py --export {wit_path}", export_path
        )
        generate_and_move(
            f"{WIT_BINDGEN_PATH} wasmtime-py --import {wit_path}", import_path
        )
        shutil.copyfile(wit_path, cached_wit_path)
