import argparse
import sys

from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from common.Instance import Instance
from apps.teams.TeamsCommand import TeamsCommand


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


def ms_main(argv):
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
