import sys
import typing


def return_error(err_message: str):
    print("ERROR: " + err_message, file=sys.stderr)
    sys.exit()


def assert_and_return(
    err_cond: bool, err_message: str, value: typing.Any
) -> typing.Any:
    if err_cond:
        print("ERROR: " + err_message, file=sys.stderr)
        sys.exit()
    else:
        return value
