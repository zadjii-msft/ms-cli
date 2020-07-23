from collections import namedtuple

"""
This is a helper type for returning tyoe things:
* whether a function was successful or not
* Some value from the function

Typically, you can return ResultAndData(True, <some_return_value>) when a
function was successful and returned a result, or ResultAndData(False,
<some_error_message>) to indicate a failure, as well as a relevant error
message.
"""


ResultAndData = namedtuple("ResultAndData", "success, data")


def Error(data=None):
    return ResultAndData(False, data)


def Success(data=None):
    return ResultAndData(True, data)
