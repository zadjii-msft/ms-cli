from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from models import db_base as base
import os
from datetime import datetime
from models.User import User
from models.ChatThread import ChatThread
from common.utils import *
from html.parser import HTMLParser

__author__ = "zadjii"


class HTMLFilter(HTMLParser):
    text = ""
    # def __init__(self):
    #     super(HTMLFilter).__init__()
    #     self.text = ""
    def handle_data(self, data):
        self.text += data


class ChatMessage(base):
    __tablename__ = "chatmessage"
    """
    Represents a single chat message
    """

    id = Column(Integer, primary_key=True)

    # From Graph API:
    graph_id = Column(String)
    body = Column(String)
    html_body = Column(String)
    thread_id = Column(Integer, ForeignKey("chatthread.id"))
    from_guid = Column(String, ForeignKey("user.guid"))
    created_date_time = Column(DateTime)
    last_modified_date_time = Column(DateTime)

    team_id = Column(String, ForeignKey("team.graph_id"))
    channel_id = Column(String, ForeignKey("channel.graph_id"))
    reply_to_id = Column(String, ForeignKey("chatmessage.graph_id"))

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
    channel = relationship(
        "Channel",
        foreign_keys=[channel_id],
        backref=backref("messages", remote_side=[channel_id], lazy="dynamic"),
    )
    replies = relationship(
        "ChatMessage", backref=backref("parent", remote_side=[graph_id]), lazy="dynamic"
    )

    @staticmethod
    def from_json(json_blob):
        result = ChatMessage()
        # print(json.dumps(json_blob, indent=2))

        result.graph_id = json_blob["id"]
        result.created_date_time = datetime_from_string(json_blob["createdDateTime"])
        result.last_modified_date_time = datetime_from_string(
            json_blob["lastModifiedDateTime"]
        )
        if json_blob["body"]["contentType"] == "html":
            result.html_body = json_blob["body"]["content"]
            f = HTMLFilter()
            f.feed(result.html_body)
            result.body = f.text
        else:
            result.body = json_blob["body"]["content"]

        result.from_guid = json_blob["from"]["user"]["id"]

        result.reply_to_id = json_blob["replyToId"]

        if "channelIdentity" in json_blob and json_blob["channelIdentity"] is not None:
            result.team_id = json_blob["channelIdentity"]["teamId"]
            result.channel_id = json_blob["channelIdentity"]["channelId"]

        return result

        # NOTE! The chat message json doesn't include the thread ID. So
        # whoever's building this should also manually stick the thread's ID
        # into it
        #
        # ... This might not be correct. It might be `chatId`, but you know
        # what, we've got it working, so we're leaving it.

    def is_channel_message(self):
        return (self.channel_id is not None) and (self.team_id is not None)

    def is_reply(self):
        return self.is_channel_message() and (self.reply_to_id is not None)

    def is_toplevel(self):
        return self.is_channel_message() and (self.reply_to_id is None)


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
    else:
        last_modified_from_json = datetime_from_string(
            msg_json["lastModifiedDateTime"]
        )
        if last_modified_from_json is not None:
            msg_model.last_modified_date_time = last_modified_from_json
            print(f'updated lmdt to {last_modified_from_json.strftime("%c")}')
            db.session.commit()

    return msg_model
