from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.MailItem import MailItem
import argparse
from argparse import Namespace
from msgraph import helpers
from tabulate import tabulate


class MailMoveCommand(BaseCommand):
    def add_parser(self, subparsers):
        list_cmd = subparsers.add_parser("mv", description="Read a message")

        list_cmd.add_argument("id")
        list_cmd.add_argument("destination")

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

        result = helpers.move_mail(graph, messageid=args.id, folderid=args.destination)

        print(result.reason)

        return Success()
