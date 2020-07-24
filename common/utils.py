
import os
import json
from datetime import datetime


def datetime_to_string(dt):
    # type: (datetime.datetime) -> str
    return (dt.isoformat() + 'Z') if dt is not None else None

def datetime_from_string(s):
    # type: (str) -> datetime.datetime
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ") if s is not None else None
