from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from models import db_base as base
import os

__author__ = "zadjii"


class User(base):
    __tablename__ = "user"
    """
    Represents a single user.
    """

    id = Column(Integer, primary_key=True)
    name = Column(String)
    # sent_messages = relationship('ChatMessage'
    #                     , backref=backref('sender', remote_side=[id])
    #                     , lazy='dynamic')
    # TODO: add some other identifying GUID, email, or whatever from graph API

    def __init__(self, username):
        self.name = username
