from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from models import db_base as base
import os

__author__ = "Mike"


class SampleModel(base):
    __tablename__ = "samplemodel"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    another_column = Column(Integer)
    some_count = Column(Integer, default=0)
    created_on = Column(DateTime)
