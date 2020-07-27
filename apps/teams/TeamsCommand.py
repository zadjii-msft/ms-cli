from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from common.Submenu import do_common_interactive_with_args
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

        return do_common_interactive_with_args("teams", self._cmd, instance, args)
