from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from models import db_base as base
import os
from datetime import datetime
from models.User import User
from common.utils import *

__author__ = "zadjii"


class ChatThread(base):
    __tablename__ = "chatthread"
    """
    Represents a single chat message
    """

    id = Column(Integer, primary_key=True)

    # From Graph API:
    # graph_id is the ID of this thread on the graph API
    graph_id = Column(String)
    topic = Column(String)
    created_date_time = Column(DateTime)
    last_updated_date_time = Column(DateTime)

    # messages is a relationship defined in ChatMessage - will return a query
    # for all the messages in this thread.

    @staticmethod
    def from_json(json_blob):
        result = ChatThread()
        result.graph_id = json_blob["id"]
        result.created_date_time = datetime_from_string(json_blob["createdDateTime"])
        result.last_updated_date_time = datetime_from_string(
            json_blob["lastUpdatedDateTime"]
        )
        result.topic = json_blob["topic"]
        return result
