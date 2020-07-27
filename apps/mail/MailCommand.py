from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from argparse import Namespace


class MailCommand(BaseCommand):
    def add_parser(self, subparsers):
        mail_cmd = subparsers.add_parser(
            "mail", description="This is the mail application"
        )

        # NOTE: For each subparser you add, the `dest` must be unique. If two
        # subparsers in the same tree of parsers share the same dest, unexpected
        # behavior is sure to follow.

        subparsers = mail_cmd.add_subparsers(
            dest="command",
            title="commands",
            description="Mail commands",
            help="Which mail command to run",
        )

        return mail_cmd

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData

        print("This is the mail command")
        return Error()
