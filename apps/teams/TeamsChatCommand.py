from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from argparse import Namespace


class TeamsChatCommand(BaseCommand):
    def add_parser(self, subparsers):
        chat_cmd = subparsers.add_parser(
            "chat", description="This is the teams chat UI"
        )

        chat_cmd.add_argument("user", help="The user to chat with")

        return chat_cmd

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData

        print("This is the teams chat command")
        user = args.user
        print(f"chatting with {user}")

        return Error()
