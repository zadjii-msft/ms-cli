from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from models import db_base as base
import os
from datetime import datetime
from models.User import User

__author__ = "zadjii"


class ChatMessage(base):
    __tablename__ = "chatmessage"
    """
    Represents a single chat message
    """

    id = Column(Integer, primary_key=True)
    content = Column(String)
    sender_id = Column(Integer, ForeignKey("user.id"))
    target_id = Column(Integer, ForeignKey("user.id"))
    timestamp = Column(DateTime)

    sender = relationship(
        "User",
        foreign_keys=[sender_id],
        backref=backref("sent_messages", remote_side=[sender_id]),
    )
    target = relationship(
        "User",
        foreign_keys=[target_id],
        backref=backref("recieved_messages", remote_side=[target_id]),
    )
    # TODO: add some other identifying GUID, email, or whatever from graph API

    def __init__(self, sender, target, message_body, sent_on=datetime.utcnow()):
        self.sender_id = sender.id
        self.target_id = target.id
        self.content = message_body
        self.timestamp = sent_on
