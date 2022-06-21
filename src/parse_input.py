import argparse
import os
import pwd
import sys
import tempfile


def check_cache_path(cache_path: str) -> str:
    cache_path = os.path.abspath(cache_path)
    if not os.path.isdir(cache_path):
        os.makedirs(cache_path)
    return cache_path


def valid_path(arg_path: str):
    """custom argparse *path file* type for user path values given from the command line"""
    if os.path.exists(arg_path):
        return os.path.abspath(arg_path)
    else:
        raise argparse.ArgumentTypeError(f"{arg_path} does not exist!")


def parse() -> tuple[str, str, str, bool, str]:
    parser = argparse.ArgumentParser(description="WASI Reactor Interface Tester")
    parser.add_argument(
        "-c",
        "--cache",
        dest="cache_path",
        type=check_cache_path,
        nargs="?",
        default=os.path.join(
            tempfile.gettempdir(), f"writ-bind-cache-{pwd.getpwuid(os.getuid())[0]}"
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
        "-b",
        "--batch",
        dest="batch_path",
        type=valid_path,
        nargs="?",
        default=None,
        required=False,
        help="path to a file containing a JSON list of row inputs",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="is_verbose",
        default=False,
        required=False,
        action="store_true",
        help="enable debug output",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        dest="is_quiet",
        default=False,
        required=False,
        action="store_true",
        help="suppress result output",
    )
    parser.add_argument(
        dest="input_args",
        nargs=argparse.REMAINDER,
        help="path to the Wasm module, function name, and arguments in JSON format",
    )
    args = parser.parse_args()
    if len(args.input_args) < 2:
        print("ERROR: Missing either wasm file path or function name.", file=sys.stderr)
        parser.print_help()
        os._exit(1)

    if args.batch_path and len(args.input_args) > 2:
        print("ERROR: Batch input (-b) may not be specified with in-line input.", file=sys.stderr)
        parser.print_help()
        os._exit(1)

    return args.cache_path, args.batch_path, args.wit_path, args.is_verbose, args.is_quiet, args.input_args
