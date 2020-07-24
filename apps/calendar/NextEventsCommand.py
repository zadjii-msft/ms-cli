from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.CalEvent import CalEvent
import argparse
from argparse import Namespace
from msgraph import helpers
from tabulate import tabulate
import os

class NextEventsCommand(BaseCommand):
    def add_parser(self, subparsers):
        list_cmd = subparsers.add_parser(
            "next", description="Gets your next several calendar events"
        )

        list_cmd.add_argument('count', nargs=argparse.REMAINDER)
        
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

        if (len(args.count) > 1):
            return Error("Too few/many paths")

        count = 3
        if args.count:
            count = int(args.count[0])

        # max 10 events
        count = min(count, 10)

        blobs = helpers.list_upcoming_events(graph, how_many=count)

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
