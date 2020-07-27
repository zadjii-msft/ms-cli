from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from common.Submenu import do_common_interactive_with_args
from argparse import Namespace

from apps.calendar.NextEventsCommand import NextEventsCommand
from apps.calendar.WeekCommand import WeekCommand


class CalendarCommand(BaseCommand):

    _cmd = None

    def add_parser(self, subparsers):
        calendar_cmd = subparsers.add_parser(
            "cal", description="This is the calendar application"
        )

        # NOTE: For each subparser you add, the `dest` must be unique. If two
        # subparsers in the same tree of parsers share the same dest, unexpected
        # behavior is sure to follow.

        subparsers = calendar_cmd.add_subparsers(
            dest="command",
            title="commands",
            description="Calendar commands",
            help="Which calendar command to run",
        )

        nextevent_cmd = NextEventsCommand(subparsers)
        week_cmd = WeekCommand(subparsers)

        self._cmd = calendar_cmd
        return calendar_cmd

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData

        return do_common_interactive_with_args("cal", self._cmd, instance, args)