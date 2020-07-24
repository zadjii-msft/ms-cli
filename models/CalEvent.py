from models import db_base as base
import datetime
from dateutil import tz
import os

__author__ = "miniksa"


class CalEvent(base):
    __tablename__ = "user"
    """
    Represents a drive item (folder or file).
    """

    def to_string(self):
        return f"{self.name} {self.type}"

    @staticmethod
    def __to_local_time(datetimestring):
        from_zone = tz.tzutc()
        to_zone = tz.tzlocal()

        datetimestr = datetimestring[:-1]
        dt = datetime.datetime.fromisoformat(datetimestr).replace(tzinfo=from_zone)

        localdt = dt.astimezone(to_zone)

        return localdt

    @staticmethod
    def from_json(json_blob):
        result = CalEvent()
        result.subject = json_blob["subject"]

        orgname = json_blob["organizer"]["emailAddress"]["name"]
        orgaddress = json_blob["organizer"]["emailAddress"]["address"]
        result.organizer = f"{orgname} <{orgaddress}>"
        result.location = json_blob["location"]["displayName"]

        result.start = CalEvent.__to_local_time(json_blob["start"]["dateTime"])
        result.end = CalEvent.__to_local_time(json_blob["end"]["dateTime"])

        return result
