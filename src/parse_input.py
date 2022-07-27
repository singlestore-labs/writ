from __future__ import annotations

import argparse
import os
import pwd
import sys
import tempfile
import textwrap


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
        raise argparse.ArgumentTypeError(f'{arg_path} does not exist!')


class LineWrapRawTextHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def _split_lines(self, text, width):
        text = self._whitespace_matcher.sub(' ', text).strip()
        return textwrap.wrap(text, 55)


def parse():
    parser = argparse.ArgumentParser(
        usage='%(prog)s [OPTIONS] WASMFILE FUNCNAME [ARGS...]',
        description='WASI Reactor Interface Tester',
        formatter_class=LineWrapRawTextHelpFormatter,
        epilog="""
Batch File Format:
  A JSON-formatted file may be passed in lieu of in-line arguments.  This file
  must consist of either a list of lists or a list of single values.  For
  example, either of the following forms will work:

  [                                    [
    "John Lennon",          OR           [ "John Lennon", "Guitar", 1940 ],
    "Paul McCartney",                    [ "Paul McCartney", "Bass", 1942 ],
    ...                                  ...
  ]                                    ]

  Each entry in the outer-most list represents the arguments for a single call
  into FUNCNAME.
""",
    )
    parser.add_argument(
        '-e',
        '--expect',
        dest='EXPECTSTR',
        default=None,
        required=False,
        help='Specifies an expected result in JSON form.'
        'If not matched, the program exits with the error code 2.'
        'May not be used with -b.',
    )
    parser.add_argument(
        '-c',
        '--cache',
        dest='CACHEDIR',
        type=check_cache_path,
        default=os.path.join(
            tempfile.gettempdir(),
            f'writ-bind-cache-{pwd.getpwuid(os.getuid())[0]}',
        ),
        required=False,
        help='Specifies a directory to use for the binding cache',
    )
    parser.add_argument(
        '-w',
        '--wit',
        dest='WITFILE',
        type=valid_path,
        default=None,
        required=False,
        help='Specifies the path to the WIT (.wit) file',
    )
    parser.add_argument(
        '-b',
        '--batch',
        dest='BATCHFILE',
        type=valid_path,
        default=None,
        required=False,
        help='Specifies a path to a file containing one or more JSON-formatted inputs'
        'to use in place of in-line arguments (see "Batch File Format", below)',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        dest='is_verbose',
        default=False,
        required=False,
        action='store_true',
        help='Enable debug output',
    )
    parser.add_argument(
        '-g',
        '--debug-info',
        dest='is_debug_info',
        default=False,
        required=False,
        action='store_true',
        help='Generate runtime debugging information for module (module must also be compiled in debug mode)',
    )
    parser.add_argument(
        '-q',
        '--quiet',
        dest='is_quiet',
        default=False,
        required=False,
        action='store_true',
        help='Suppress result output',
    )
    parser.add_argument(
        dest='WASMFILE',
        help='Specifies the path to the Wasm module (.wasm file)',
    )
    parser.add_argument(
        dest='FUNCNAME',
        help='Specifies the name of the Wasm function to run',
    )
    parser.add_argument(
        dest='ARGS',
        nargs=argparse.REMAINDER,
        help='Specifies 0 or more arguments to pass into the Wasm function. '
        'Complex arguments may be expressed in JSON format.  May not be used with the -b option',
    )
    args = parser.parse_args()
    if args.BATCHFILE and len(args.ARGS) > 0:
        print(
            'ERROR: Batch input (-b) may not be specified with in-line input.',
            file=sys.stderr,
        )
        parser.print_help()
        sys.exit(1)
    if args.BATCHFILE and args.EXPECTSTR is not None:
        print(
            'ERROR: Batch input (-b) may not be specified with an expected result (-e).',
            file=sys.stderr,
        )
        parser.print_help()
        sys.exit(1)

    return args
