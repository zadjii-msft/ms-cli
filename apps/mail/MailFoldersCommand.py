from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.MailFolder import MailFolder
import argparse
from argparse import Namespace
from msgraph import helpers
from tabulate import tabulate


class MailFoldersCommand(BaseCommand):
    def add_parser(self, subparsers):
        list_cmd = subparsers.add_parser("folders", description="List folders")

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

        folders = helpers.list_mail_folders(graph)

        items = []
        for item in folders["value"]:
            mailFolder = MailFolder.from_json(item)
            items.append(mailFolder)

        table = []
        for i in items:
            q = [i.name, i.children, i.unread, i.total, i.id]
            table.append(q)

        print(
            tabulate(
                table,
                headers=[
                    "Name",
                    "# of Children",
                    "# of Unread Msg",
                    "# of Msg (total)",
                    "ID",
                ],
            )
        )

        return Success()
