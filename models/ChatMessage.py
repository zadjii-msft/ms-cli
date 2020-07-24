from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from models import db_base as base
import os
from datetime import datetime
from models.User import User
from models.ChatThread import ChatThread
from common.utils import *

__author__ = "zadjii"


class ChatMessage(base):
    __tablename__ = "chatmessage"
    """
    Represents a single chat message
    """

    id = Column(Integer, primary_key=True)

    # From Graph API:
    graph_id = Column(String)
    body = Column(String)
    thread_id = Column(Integer, ForeignKey("chatthread.id"))
    from_guid = Column(String, ForeignKey("user.guid"))
    created_date_time = Column(DateTime)
    last_modified_date_time = Column(DateTime)

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
        result.created_date_time = datetime_from_string(json_blob["createdDateTime"])
        result.last_modified_date_time = datetime_from_string(
            json_blob["lastModifiedDateTime"]
        )
        result.body = json_blob["body"]["content"]
        result.from_guid = json_blob["from"]["user"]["id"]
        return result

        # NOTE! The chat message json doesn't include the thread ID. So
        # whoever's building this should also manually stick the thread's ID
        # into it
        #
        # ... This might not be correct. It might be `chatId`, but you know
        # what, we've got it working, so we're leaving it.


def get_or_create_message_model(db, msg_json):
    # type: (SimpleDB, json) -> ChatMessage
    id_from_json = msg_json["id"]
    msg_model = (
        db.session.query(ChatMessage)
        .filter(ChatMessage.graph_id == id_from_json)
        .first()
    )
    if msg_model is None:
        msg_model = ChatMessage.from_json(msg_json)
        db.session.add(msg_model)
        db.session.commit()
    return msg_model
