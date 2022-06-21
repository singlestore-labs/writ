import os
import sys
from enum import Enum

def eprint(s):
    print(s, file=sys.stderr)

def abort(s):
    eprint(s)
    os._exit(1)

class ErrorCode(Enum):
    INITIALIZE_MODULE_FAILED = 1
    INVOKE_INITIALIZE_FAILED = 2
    MISSING_INPUT = 3
    OBJECT_NOT_FOUND = 4
    PATH_NOT_EXIST = 5
    TYPE_NOT_IMPLEMENTED = 6
    WRONG_ARGS = 7
    ARG_TYPE_NOT_IMPLEMENTED = 8
    DUMP_JSON_FAILED = 9
    LOAD_JSON_FAILED = 10
    TYPE_MISMATCH = 11
    TYPE_TO_STRING_NOT_IMPLEMENTED = 12
    PYOBJ_TO_PYSTR_FAILED = 13
    UNKNOWN = 14
    EMPTY_STRING = 15
    VARIABLE_NOT_IN_PATH = 16
    PATH_NOT_EXECUTABLE = 17


class Error(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg
