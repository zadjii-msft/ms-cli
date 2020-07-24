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

    # From Graph API:
    guid = Column(String)
    display_name = Column(String)
    user_principal_name = Column(String)
    mail = Column(String)

    @staticmethod
    def from_json(json_blob):
        result = User()
        result.guid = json_blob["id"]
        result.display_name = json_blob["displayName"]
        result.user_principal_name = json_blob["userPrincipalName"]
        result.mail = json_blob["mail"]
        return result


def get_or_create_user_model(db, user_json):
    # type: (SimpleDB, json) -> User
    id_from_json = user_json["id"]
    user_model = db.session.query(User).filter(User.guid == id_from_json).first()
    if user_model is None:
        user_model = User.from_json(user_json)
        db.session.add(user_model)
        db.session.commit()
    return user_model
