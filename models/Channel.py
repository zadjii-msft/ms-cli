from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from models import db_base as base
from models.Team import Team
from models.ChatMessage import ChatMessage
import os

__author__ = "zadjii"


class Channel(base):
    __tablename__ = "channel"
    """
    Represents a single channel within a team.
    """

    id = Column(Integer, primary_key=True)

    last_cached = Column(DateTime)

    # From Graph API:
    graph_id = Column(String)
    display_name = Column(String)
    team_id = Column(String, ForeignKey("team.graph_id"))

    team = relationship(
        "Team",
        foreign_keys=[team_id],
        backref=backref("channels", remote_side=[team_id], lazy="dynamic"),
    )

    @staticmethod
    def from_json(json_blob):
        result = Channel()
        result.graph_id = json_blob["id"]
        result.display_name = json_blob["displayName"]
        return result

    def last_modified_time(self):
        # messages_by_recency = self.messages.order_by(ChatMessage.last_modified_date_time.desc())
        # [print(f'{m.last_modified_date_time.strftime("%c") if m.last_modified_date_time is not None else "None"}') for m in messages_by_recency]
        # most_recent = messages_by_recency.first()
        # return most_recent.last_modified_date_time
        return self.last_cached


def get_or_create_channel_model(db, channel_json):
    # type: (SimpleDB, json) -> Channel
    id_from_json = channel_json["id"]
    channel_model = (
        db.session.query(Channel).filter(Channel.graph_id == id_from_json).first()
    )
    if channel_model is None:
        channel_model = Channel.from_json(channel_json)
        db.session.add(channel_model)
        db.session.commit()

    return channel_model
