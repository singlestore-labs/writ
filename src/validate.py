"""
validate path, user input, etc
"""
from __future__ import annotations

import filecmp
import os
import shutil
import subprocess
import tempfile
import typing
from enum import Enum

import error_handler
import validate


class ErrorCode(Enum):
    EMPTY_STRING = 'Empty string or string not found.'
    VARIABLE_DOES_NOT_EXIST = 'Missing the following variable in PATH: '
    PATH_NOT_EXECUTABLE = 'The following path is not executable: '


def resolve_string(s: typing.Optional[str]) -> str:
    if s is None:
        raise error_handler.Error(
            error_handler.ErrorCode.EMPTY_STRING,
            f'String {s} is empty or not found.',
        )
    return str(s)


def check_command(env_name: str, command: str) -> typing.Optional[str]:
    ENV_CMD = os.environ.get(env_name)
    if ENV_CMD is not None:
        return ENV_CMD
    path = shutil.which(command)
    if path is None:
        error_handler.Error(
            error_handler.ErrorCode.VARIABLE_NOT_IN_PATH,
            f'{command} does not exist in path.',
        )
    if not os.access(os.path.abspath(validate.resolve_string(path)), os.X_OK):
        error_handler.Error(
            error_handler.ErrorCode.PATH_NOT_EXECUTABLE,
            f'The following path is not executable: {path}',
        )
    return path


def generate_and_move(
    command: list[str],
    src_dir: str,
    dst_path: str,
    is_verbose: bool,
):
    try:
        subprocess.run(command, capture_output=not is_verbose)
        if is_verbose:
            print('Invoking command {}'.format(command))
        src_path = os.path.join(src_dir, 'bindings.py')
        if is_verbose:
            print('Copying {} to {}'.format(src_path, dst_path))
        shutil.copy(src_path, dst_path)
        os.remove(src_path)
    except Exception:
        raise error_handler.Error(
            error_handler.ErrorCode.UNKNOWN,
            'Unknown error when running the command, likely caused by wrong/unmatched wit specification.',
        )


def check_cached_file_or_generate(
    WIT_BINDGEN_PATH: typing.Optional[str],
    wit_path: str,
    cached_wit_path: str,
    export_path: str,
    import_path: str,
    is_verbose: bool,
) -> None:
    if is_verbose:
        print('Comparing {} to {}'.format(cached_wit_path, wit_path))
    if not os.path.exists(cached_wit_path) or not filecmp.cmp(
        cached_wit_path,
        wit_path,
        shallow=False,
    ):
        tmp_dir = tempfile.mkdtemp()
        try:
            generate_and_move(
                [
                    validate.resolve_string(WIT_BINDGEN_PATH),
                    'wasmtime-py',
                    '--export',
                    wit_path,
                    '--out-dir',
                    tmp_dir,
                ],
                tmp_dir,
                export_path,
                is_verbose,
            )
            generate_and_move(
                [
                    validate.resolve_string(WIT_BINDGEN_PATH),
                    'wasmtime-py',
                    '--import',
                    wit_path,
                    '--out-dir',
                    tmp_dir,
                ],
                tmp_dir,
                import_path,
                is_verbose,
            )
            shutil.copyfile(wit_path, cached_wit_path)
        finally:
            os.rmdir(tmp_dir)
