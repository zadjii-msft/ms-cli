from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.CalEvent import CalEvent
import argparse
from argparse import Namespace
from msgraph import helpers
from tabulate import tabulate
import datetime
import os

class WeekCommand(BaseCommand):
    def add_parser(self, subparsers):
        list_cmd = subparsers.add_parser(
            "week", description="Gets your week at a glance"
        )

        return list_cmd

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        db = instance.get_db()
        instance.login_to_graph()

        rd = instance.get_current_user()
        if not rd.success:
            return Error("no logged in user")
        current_user = rd.data

        graph = instance.get_graph_session()

        today = datetime.date.today()
        start = today - datetime.timedelta(days=today.weekday())
        end = start + datetime.timedelta(days=6)

        startdt = datetime.datetime.combine(start, datetime.datetime.min.time())
        enddt = datetime.datetime.combine(end, datetime.datetime.max.time())

        blobs = helpers.list_events_in_time_range(graph, start=startdt, end=enddt)

        events = []

        for blob in blobs['value']:
            e = CalEvent.from_json(blob)
            events.append(e)

        table = []

        for e in events:
            row = [e.subject, e.start.strftime("%c"), e.end.strftime("%c"), e.location, e.organizer]
            table.append(row)

        print(tabulate(table, headers=["Title", "Start Time", "End Time", "Location", "Created By"]))

        return Success()
