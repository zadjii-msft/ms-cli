import argparse
import sys
import os
import json
import datetime

import sys as _sys

from gettext import gettext as _, ngettext

from msgraph import helpers

from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from common.Instance import Instance
from common.CaughtParserError import CaughtParserError
import common.ParserState
from apps.teams.TeamsCommand import TeamsCommand
from apps.teams.LogoutCommand import LogoutCommand
from apps.onedrive.OnedriveCommand import OnedriveCommand
from apps.calendar.CalendarCommand import CalendarCommand
from apps.mail.MailCommand import MailCommand


# Turns VT output support on
def enable_vt_support():
    if os.name == "nt":
        import ctypes

        hOut = ctypes.windll.kernel32.GetStdHandle(-11)
        out_modes = ctypes.c_uint32()
        ENABLE_VT_PROCESSING = ctypes.c_uint32(0x0004)
        # ctypes.addressof()
        ctypes.windll.kernel32.GetConsoleMode(hOut, ctypes.byref(out_modes))
        out_modes = ctypes.c_uint32(out_modes.value | 0x0004)
        ctypes.windll.kernel32.SetConsoleMode(hOut, out_modes)


class MigrateCommand(BaseCommand):
    def add_parser(self, subparsers):
        sample = subparsers.add_parser(
            "migrate", description="Used to update the database"
        )
        return sample

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        instance.migrate()
        # TODO: Does this even work? I have no idea
        return Error()


# See https://docs.python.org/3/library/argparse.html#exiting-methods, used to override exit behavior if we want.
class ErrorCatchingArgumentParser(argparse.ArgumentParser):
    def exit(self, status=0, message=None):
        if message:
            self._print_message(message, _sys.stderr)
        _sys.exit(status)

    def error(self, message):
        if common.ParserState.doExitOnError:
            self.print_usage(_sys.stderr)
            args = {"prog": self.prog, "message": message}
            self.exit(2, _("%(prog)s: error: %(message)s\n") % args)
        else:
            raise CaughtParserError(message=message)

    def format_apps_help(self):
        formatter = self._get_formatter()

        # positionals, optionals and user-defined groups
        for action_group in self._action_groups[2:]:
            # if action_group.title == "apps":
            formatter.start_section(action_group.title)
            formatter.add_text(action_group.description)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        # determine help from format above
        return formatter.format_help()

    def print_apps_help(self, file=None):
        if file is None:
            file = _sys.stdout
        self._print_message(self.format_apps_help(), file)


def build_arg_parser():
    root_parser = ErrorCatchingArgumentParser(add_help=False)

    apps_parser = ErrorCatchingArgumentParser(parents=[root_parser])

    # NOTE: For each subparser you add, the `dest` must be unique. If two
    # subparsers in the same tree of parsers share the same dest, unexpected
    # behavior is sure to follow.
    subparsers = apps_parser.add_subparsers(
        dest="app",
        title="apps",
        description="Application commands",
        help="Which graph application to run",
    )
    teams_cmd = TeamsCommand(subparsers)
    onedrive_cmd = OnedriveCommand(subparsers)
    calendar_cmd = CalendarCommand(subparsers)
    mail_cmd = MailCommand(subparsers)

    MigrateCommand(subparsers)
    LogoutCommand(subparsers)
    return apps_parser


def dostuff2(instance):
    instance.login_to_graph()
    session = instance.get_graph_session()

    # teams = helpers.list_joined_teams(session)
    # print(teams)

    # team_id = teams["value"][0]["id"]
    # print(team_id)

    # channels = helpers.list_channels(session, team_id=team_id)
    # print(channels)

    # channel_id = channels["value"][0]["id"]
    # print(channel_id)

    # response = helpers.list_channel_messages_since_time(session, team_id=team_id, channel_id = channel_id)
    # response2 = helpers.list_channel_messages_since_delta(session, deltaLink = response["@odata.deltaLink"])

    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)

    # response = helpers.list_channel_messages_since_time(session, team_id=team_id, channel_id = channel_id, when=yesterday)
    # print(response)

    # response = helpers.send_message(session, team_id=team_id, channel_id=channel_id, message="foobarbaz")
    # print(response)

    chats = helpers.list_chats(session)
    # print(chats)
    print(json.dumps(chats, indent=2))

    chat_id = chats["value"][0]["id"]

    response = helpers.list_chat_messages_since_time(session, chat_id=chat_id)
    print(response)

    # response = helpers.list_chat_messages_since_time(session, chat_id=chat_id)

    # # response = helpers.send_message(session, team_id=team_id, channel_id=chat_id, message="farts")
    # response = helpers.send_chat_message(
    #     session,
    #     chat_id=chat_id,
    #     message="hey michael this is a message mike using the tool",
    # )
    # print(response)

    # messages = helpers.list_chat_messages(session, chat_id=chat_id)

    # print(messages)
    print(json.dumps(messages, indent=2))
    exit()


def ms_main(argv):

    enable_vt_support()

    parser = build_arg_parser()
    args = parser.parse_args()

    if args.app == None:
        common.ParserState.doExitOnError = False
        while True:
            print("ms>", end=" ")
            command = input().split(" ")

            if len(command) == 1:
                c = command[0].lower()

                if c == "help":
                    parser.print_apps_help()
                    continue

                if c == "exit" or c == "quit":
                    print("Goodbye!")
                    sys.exit(0)

            try:
                args = parser.parse_args(args=command)

                if args.func:
                    instance = Instance()
                    result = args.func(instance, args)
                    if result is not None:
                        if not result.success:
                            if result.data:
                                print("\x1b[31m")
                                print(result.data)
                                print("\x1b[m")
                else:
                    print("Invalid command")
            except CaughtParserError as e:
                print(e)

        return

    if args.func:
        instance = Instance()
        result = args.func(instance, args)
        if result is not None:
            if result.success:
                sys.exit(0)
            else:
                if result.data:
                    print("\x1b[31m")
                    print(result.data)
                    print("\x1b[m")
                sys.exit(-1)
        else:
            sys.exit(-1)

    else:
        print(
            "Programming error - The command you entered didnt supply a implementation"
        )
        print("Go add a `set_defaults(func=DO_THE_THING)` to {}".format(args.command))
    return


if __name__ == "__main__":
    ms_main(sys.argv)
