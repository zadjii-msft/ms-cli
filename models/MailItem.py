from models import db_base as base
import datetime
from dateutil import tz
import os

__author__ = "miniksa"


class MailItem(base):
    __tablename__ = "user"
    """
    Represents a mail item 
    """

    def to_string(self):
        return f"{self.subject} {self.sender}"

    @staticmethod
    def __to_local_time(datetimestring):
        from_zone = tz.tzutc()
        to_zone = tz.tzlocal()

        datetimestr = datetimestring.rstrip("Z")
        dt = datetime.datetime.fromisoformat(datetimestr).replace(tzinfo=from_zone)

        localdt = dt.astimezone(to_zone)

        return localdt

    @staticmethod
    def from_json(json_blob):
        result = MailItem()
        result.subject = json_blob["subject"]

        result.id = json_blob["id"]

        if "body" in json_blob:
            body = json_blob["body"]
            if "content" in body:
                result.body = body["content"]

        sendername = json_blob["sender"]["emailAddress"]["name"]
        senderaddr = json_blob["sender"]["emailAddress"]["address"]

        result.sender = f"{sendername} <{senderaddr}>"
        result.when = MailItem.__to_local_time(json_blob["receivedDateTime"])

        return result
