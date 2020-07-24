import argparse
import sys
import os
import json
import datetime

from msgraph import helpers

from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from common.Instance import Instance
from apps.teams.TeamsCommand import TeamsCommand
from apps.onedrive.OnedriveCommand import OnedriveCommand


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


def build_arg_parser():
    root_parser = argparse.ArgumentParser(add_help=False)

    apps_parser = argparse.ArgumentParser(parents=[root_parser])

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
    
    MigrateCommand(subparsers)
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

    #response = helpers.list_channel_messages_since_time(session, team_id=team_id, channel_id = channel_id)
    #response2 = helpers.list_channel_messages_since_delta(session, deltaLink = response["@odata.deltaLink"])

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
        # TODO: boot straight to the ms-cli
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
