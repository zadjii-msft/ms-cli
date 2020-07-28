from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from common.Submenu import do_common_interactive_with_args
from argparse import Namespace
from apps.mail.MailListCommand import MailListCommand
from apps.mail.MailFoldersCommand import MailFoldersCommand
from apps.mail.MailReadCommand import MailReadCommand


class MailCommand(BaseCommand):

    _cmd = None

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

        list_cmd = MailListCommand(subparsers)
        folders_cmd = MailFoldersCommand(subparsers)
        read_cmd = MailReadCommand(subparsers)

        self._cmd = mail_cmd
        return mail_cmd

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        return do_common_interactive_with_args("mail", self._cmd, instance, args)
