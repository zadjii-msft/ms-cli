import argparse
import sys
import json
from msgraph import helpers

from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from common.Instance import Instance
from apps.teams.TeamsCommand import TeamsCommand

SECRETS_FILE = "secrets.json"
CONFIG_FILE = "config.json"

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
    return apps_parser


def login_flow(*, secrets):
    session = helpers.device_flow_session_msal(
        secrets["MS_GRAPH_CLIENT_ID"], secrets["MS_GRAPH_SCOPES"]
    )
    if not session:
        raise Exception("Couldn't connect to graph.")
    return session

def get_app_config():
    secrets = json.load(open(SECRETS_FILE, "r", encoding="utf-8"))
    config  = json.load(open(CONFIG_FILE, "r", encoding="utf-8"))

    appconfig = {}
    appconfig.update(secrets)
    appconfig.update(config)
    return appconfig

def dostuff():
    appconfig = get_app_config()
    session = login_flow(secrets=appconfig)

    teams = helpers.list_joined_teams(session)
    print(teams)

    team_id = teams['value'][0]['id']
    print(team_id)

    channels = helpers.list_channels(session, team_id=team_id)
    print(channels)

    channel_id = channels['value'][0]['id']
    print(channel_id)

    # response = helpers.send_message(session, team_id=team_id, channel_id=channel_id, message="foobarbaz")
    # print(response)

    chats = helpers.list_chats(session)
    print(chats)

    chat_id = chats['value'][0]['id']

    # response = helpers.send_message(session, team_id=team_id, channel_id=chat_id, message="farts")
    response = helpers.send_chat_message(session, chat_id=chat_id, message="hey mike this is a message coming from the tool")
    print(response)

    # messages = helpers.list_chat_messages(session, chat_id=chat_id)

    # print(messages)

    exit()

def ms_main(argv):
    dostuff()

    parser = build_arg_parser()
    args = parser.parse_args()

    if args.app == None:
        # TODO: boot straight to the ms-cli
        return

    if args.func:
        # TODO: If there's any authentication state we'll need to set up
        # regardless of what command we're running, we should build some sort of
        # common "instance" state, and use this first arg to pass it to the
        # command
        #
        # This "instance" would also include things like an active DB instance

        instance = Instance()
        result = args.func(instance, args)
        if result is not None:
            if result.success:
                sys.exit(0)
            else:
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
