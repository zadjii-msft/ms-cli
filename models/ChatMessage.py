from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from models import db_base as base
import os
from datetime import datetime
from models.User import User
from models.ChatThread import ChatThread

__author__ = "zadjii"


class ChatMessage(base):
    __tablename__ = "chatmessage"
    """
    Represents a single chat message
    """

    id = Column(Integer, primary_key=True)

    graph_id = Column(String)
    body = Column(String)
    thread_id = Column(Integer, ForeignKey("chatthread.id"))
    from_guid = Column(String, ForeignKey("user.guid"))
    created_date_time = Column(DateTime)

    sender = relationship(
        "User",
        foreign_keys=[from_guid],
        backref=backref("sent_chat_messages", remote_side=[from_guid], lazy="dynamic"),
    )
    thread = relationship(
        "ChatThread",
        foreign_keys=[thread_id],
        backref=backref("messages", remote_side=[thread_id], lazy="dynamic"),
    )

    @staticmethod
    def from_json(json_blob):
        result = ChatMessage()
        result.graph_id = json_blob["id"]
        # result.created_date_time = TODO: convert string ("2020-07-23T17:07:17.047Z") to datetime
        # result.last_updated_time = TODO: convert string ("2020-07-23T17:07:17.047Z") to datetime
        result.body = json_blob["body"]["content"]
        result.from_guid = json_blob["from"]["user"]["id"]
        return result

    # NOTE! The chat message json doesn't include the thread ID. So whoever's building this should also manually stick the thread's ID into it
