import argparse
import json
import os
import pwd


def check_binding_path(binding_path: str) -> str:
    if binding_path[-1] != "/":
        binding_path += "/"
    if not os.path.isdir(binding_path):
        os.makedirs(binding_path)
    return binding_path


def set_default_binding_path(ENV_NAME, DEFAULT_PATH: str) -> str:
    ENV_PATH = os.environ.get(ENV_NAME)
    if ENV_PATH is not None:
        return ENV_PATH
    return DEFAULT_PATH


def valid_path(arg_path: str):
    """custom argparse *path file* type for user path values given from the command line"""
    if os.path.exists(arg_path):
        return arg_path
    else:
        raise argparse.ArgumentTypeError(f"{arg_path} does not exist!")


def parse():
    parser = argparse.ArgumentParser(description="WASI Reactor Interface Tester")
    parser.add_argument(
        "-b",
        "--bindings",
        dest="binding_path",
        type=check_binding_path,
        nargs="?",
        default=set_default_binding_path(
            "WRIT_WITBINDGEN_PATH",
            f"/tmp/writ-bind-cache-{pwd.getpwuid(os.getuid())[0]}/",
        ),
        required=False,
        help="directory path to use for the binding cache",
    )
    parser.add_argument(
        "-w",
        "--wit",
        dest="wit_path",
        type=valid_path,
        nargs="?",
        default=None,
        required=False,
        help="path to the WIT file",
    )
    parser.add_argument(
        dest="input_args",
        nargs=argparse.REMAINDER,
        help="path to the Wasm module, function name, and arguments in JSON format",
    )
    args = parser.parse_args()
    return args.binding_path, args.wit_path, args.input_args
