from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.CalEvent import CalEvent
import argparse
from argparse import Namespace
from msgraph import helpers
from tabulate import tabulate
import datetime
import os
import parsedatetime


class NewEventCommand(BaseCommand):
    def add_parser(self, subparsers):
        list_cmd = subparsers.add_parser(
            "new", description="Makes a new event"
        )

        list_cmd.add_argument("event")
        list_cmd.add_argument("location")
        list_cmd.add_argument("duration")
        list_cmd.add_argument("start", nargs=argparse.REMAINDER)

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

        name = args.event
        starttext = " ".join(args.start)
        durationtext = args.duration
        locationtext = args.location
        
        cal = parsedatetime.Calendar()

        start = cal.parseDT(starttext)[0]

        end = cal.parseDT(durationtext, sourceTime=start)[0]

        # convert starttext to start datetime (local)

        # convert durationtext into time span

        #find end time from start + duration

        #call command

        response = helpers.create_event(graph, subject=name, location=locationtext, start=start, end=end)

        print(response.reason)

        return Success()
