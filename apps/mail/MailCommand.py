from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from common.CaughtParserError import CaughtParserError
from argparse import Namespace


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

        self._cmd = mail_cmd
        return mail_cmd

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData

        while True:
            print("ms mail>", end=" ")
            command = input().split(" ")

            if (len(command) == 1 and (command[0].lower() == "exit" or command[0].lower() == "quit")):
                print('Returning to main menu...')
                break

            try:
                args = self._cmd.parse_args(args=command)

                if args.func:
                    result = args.func(instance, args)
                    if result is not None:
                        if not result.success:
                            if result.data:
                                print("\x1b[31m")
                                print(result.data)
                                print("\x1b[m")
                else:
                    print('Invalid command')
            except CaughtParserError as e:
                print(e)
                
        return Error()
