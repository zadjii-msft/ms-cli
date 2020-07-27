from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from common.CaughtParserError import CaughtParserError
from argparse import Namespace
from apps.teams.DirectChatCommand import DirectChatCommand
from apps.teams.TeamsCacheCommand import TeamsCacheCommand
from apps.teams.ListTeamsCommand import ListTeamsCommand
from apps.teams.TeamsTeamCommand import TeamsTeamCommand
from apps.teams.TeamChatCommand import TeamChatCommand


class TeamsCommand(BaseCommand):

    _cmd = None

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
        teams_chat_cmd = DirectChatCommand(subparsers)
        teams_cache_cmd = TeamsCacheCommand(subparsers)
        ListTeamsCommand(subparsers)
        TeamsTeamCommand(subparsers)
        TeamChatCommand(subparsers)
        self._cmd = teams_cmd
        return teams_cmd

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData

        while True:
            print("ms teams>", end=" ")
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
