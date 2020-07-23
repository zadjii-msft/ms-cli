from collections import namedtuple

ResultAndData = namedtuple('ResultAndData', 'success, data')

def Error(data=None):
    return ResultAndData(False, data)

def Success(data=None):
    return ResultAndData(True, data)
