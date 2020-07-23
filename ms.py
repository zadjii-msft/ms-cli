import argparse
import sys
import os

from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from common.Instance import Instance
from apps.teams.TeamsCommand import TeamsCommand

# Turns VT output support on
def enable_vt_support():
    if os.name == 'nt':
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
    MigrateCommand(subparsers)
    return apps_parser


def ms_main(argv):
    enable_vt_support()
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
                print('\x1b[31m')
                print(result.data)
                print('\x1b[m')
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
