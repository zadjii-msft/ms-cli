from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from models import db_base as base
import os

__author__ = "zadjii"


class Team(base):
    __tablename__ = "team"
    """
    Represents a single team.
    """

    id = Column(Integer, primary_key=True)

    # From Graph API:
    graph_id = Column(String)
    display_name = Column(String)

    @staticmethod
    def from_json(json_blob):
        result = Team()
        result.graph_id = json_blob["id"]
        result.display_name = json_blob["displayName"]
        return result

    def get_channels_json(self, graph):
        from msgraph import helpers

        channels = helpers.list_channels(graph, team_id=self.graph_id)
        return channels


def get_or_create_team_model(db, team_json):
    # type: (SimpleDB, json) -> Team
    id_from_json = team_json["id"]
    team_model = db.session.query(Team).filter(Team.graph_id == id_from_json).first()
    if team_model is None:
        team_model = Team.from_json(team_json)
        db.session.add(team_model)
        db.session.commit()
    return team_model
