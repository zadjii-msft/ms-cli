from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from argparse import Namespace
from apps.teams.TeamsChatCommand import TeamsChatCommand


class TeamsCommand(BaseCommand):
    def add_parser(self, subparsers):
        teams_cmd = subparsers.add_parser(
            "teams", description="This is the teams application"
        )

        # NOTE: For each subparser you add, the `dest` must be unique. If two
        # subparsers in the same tree of parsers share the same dest, unexpected
        # behavior is sure to follow.

        subparsers = teams_cmd.add_subparsers(
            dest="command",
            title="commands",
            description="Teams commands",
            help="Which teams command to run",
        )
        teams_chat_cmd = TeamsChatCommand(subparsers)
        return teams_cmd

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData

        print("This is the teams command")
        return Error()
