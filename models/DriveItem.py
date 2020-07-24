from models import db_base as base
import datetime
from dateutil import tz
import os

__author__ = "miniksa"


class DriveItem(base):
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

        datetimestr = datetimestring.rstrip('Z')
        dt = datetime.datetime.fromisoformat(datetimestr).replace(tzinfo=from_zone)

        localdt = dt.astimezone(to_zone)

        return localdt

    @staticmethod
    def from_json(json_blob):
        result = DriveItem()
        result.name = json_blob["name"]
        result.size = json_blob["size"]
        result.id = json_blob["id"]

        result.created = DriveItem.__to_local_time(json_blob["fileSystemInfo"]["createdDateTime"])
        result.modified = DriveItem.__to_local_time(json_blob["fileSystemInfo"]["lastModifiedDateTime"])

        if "folder" in json_blob:
            result.type = "folder"
            result.children = json_blob["folder"]["childCount"]
        elif "file" in json_blob:
            result.type = "file"
            result.download = json_blob["@microsoft.graph.downloadUrl"]


        return result
