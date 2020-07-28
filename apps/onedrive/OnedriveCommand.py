from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from common.Submenu import do_common_interactive_with_args
from argparse import Namespace
from apps.onedrive.OnedriveGetCommand import OnedriveGetCommand
from apps.onedrive.OnedrivePutCommand import OnedrivePutCommand
from apps.onedrive.OnedriveDeleteCommand import OnedriveDeleteCommand
from apps.onedrive.OnedriveRenameCommand import OnedriveRenameCommand
from apps.onedrive.OnedriveMakeDirCommand import OnedriveMakeDirCommand
from apps.onedrive.OnedriveListCommand import OnedriveListCommand


class OnedriveCommand(BaseCommand):

    _cmd = None

    def add_parser(self, subparsers):
        onedrive_cmd = subparsers.add_parser(
            "onedrive", description="This is the onedrive application"
        )

        # NOTE: For each subparser you add, the `dest` must be unique. If two
        # subparsers in the same tree of parsers share the same dest, unexpected
        # behavior is sure to follow.

        subparsers = onedrive_cmd.add_subparsers(
            dest="command",
            title="commands",
            description="Onedrive commands",
            help="Which onedrive command to run",
        )
        onedrive_get_cmd = OnedriveGetCommand(subparsers)
        onedrive_put_cmd = OnedrivePutCommand(subparsers)
        onedrive_delete_cmd = OnedriveDeleteCommand(subparsers)
        onedrive_rename_cmd = OnedriveRenameCommand(subparsers)
        onedrive_makedir_cmd = OnedriveMakeDirCommand(subparsers)
        onedrive_list_cmd = OnedriveListCommand(subparsers)

        self._cmd = onedrive_cmd
        return onedrive_cmd

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        return do_common_interactive_with_args("onedrive", self._cmd, instance, args)
