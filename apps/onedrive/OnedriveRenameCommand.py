from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.DriveItem import DriveItem
import argparse
from argparse import Namespace
from msgraph import helpers
import requests
import os


class OnedriveRenameCommand(BaseCommand):
    def add_parser(self, subparsers):
        list_cmd = subparsers.add_parser(
            "mv", description="Renames/moves an item in OneDrive"
        )

        list_cmd.add_argument("path", help="path to the item")
        list_cmd.add_argument("name", help="new name for the item")

        return list_cmd

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        db = instance.get_db()
        instance.login_to_graph()

        rd = instance.get_current_user()
        if not rd.success:
            return Error("no logged in user")
        current_user = rd.data

        graph = instance.get_graph_session()

        newname = args.name

        item = helpers.get_item(graph, path=args.path.replace("\\", "/"))
        driveitem = DriveItem.from_json(item)

        print(f"Renaming {driveitem.name} to {newname}...")

        helpers.rename_item(graph, item_id=driveitem.id, newname=newname)

        print(f"Done")

        return Success()
