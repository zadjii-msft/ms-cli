from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.MailItem import MailItem
import argparse
from argparse import Namespace
from msgraph import helpers
from tabulate import tabulate


class MailSearchCommand(BaseCommand):
    def add_parser(self, subparsers):
        list_cmd = subparsers.add_parser("search", description="Read a message")

        list_cmd.add_argument("query")

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

        mail = helpers.list_mail(
            graph, select="subject,sender,receivedDateTime", search=args.query
        )

        items = []
        for item in mail["value"]:
            mailItem = MailItem.from_json(item)
            items.append(mailItem)

        table = []
        for i in items:
            q = [i.when, i.sender, i.subject, i.id]
            table.append(q)

        print(tabulate(table, headers=["Received", "Sender", "Subject", "ID"]))

        return Success()
