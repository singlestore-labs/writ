import argparse
import json
import os


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
        type=valid_path,
        nargs="?",
        default="/var/tmp/",
        required=False,
        help="path to the binding folder",
    )
    parser.add_argument(
        "-w",
        "--wit",
        dest="wit_path",
        type=valid_path,
        nargs="?",
        default=None,
        required=False,
        help="path to the wit file",
    )
    parser.add_argument(
        dest="input_args",
        nargs=argparse.REMAINDER,
        help="path to the wasm file, function name, input in json format",
    )
    args = parser.parse_args()
    return args.binding_path, args.wit_path, args.input_args
