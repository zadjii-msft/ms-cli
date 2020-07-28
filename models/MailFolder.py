from models import db_base as base
import datetime
from dateutil import tz
import os

__author__ = "miniksa"


class MailFolder(base):
    __tablename__ = "user"
    """
    Represents a mail folder 
    """

    def to_string(self):
        return f"{self.name}"

    @staticmethod
    def from_json(json_blob):
        result = MailFolder()
        result.id = json_blob["id"]
        result.name = json_blob["displayName"]
        result.parent = json_blob["parentFolderId"]
        result.children = json_blob["childFolderCount"]
        result.unread = json_blob["unreadItemCount"]
        result.total = json_blob["totalItemCount"]

        return result
