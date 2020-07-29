from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.MailItem import MailItem
import argparse
from argparse import Namespace
from msgraph import helpers
from tabulate import tabulate


class MailSendCommand(BaseCommand):
    def add_parser(self, subparsers):
        list_cmd = subparsers.add_parser("send", description="Read a message")

        list_cmd.add_argument("to")
        list_cmd.add_argument("subject")
        list_cmd.add_argument("message", nargs=argparse.REMAINDER)

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

        recipients = args.to.split(";")

        msg = " ".join(args.message)

        result = helpers.send_mail(
            graph,
            subject=args.subject,
            recipients=recipients,
            body=msg,
            content_type="text",
        )

        print(result.reason)

        return Success()
