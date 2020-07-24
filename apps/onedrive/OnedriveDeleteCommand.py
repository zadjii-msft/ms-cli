from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.DriveItem import DriveItem
import argparse
from argparse import Namespace
from msgraph import helpers
import requests
import os

class OnedriveDeleteCommand(BaseCommand):
    def add_parser(self, subparsers):
        list_cmd = subparsers.add_parser(
            "del", description="Deletes an item out of OneDrive (sends to recycle bin)"
        )

        list_cmd.add_argument('path', nargs=argparse.REMAINDER)
        
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

        if (len(args.path) != 1):
            return Error("Too few/many paths")

        item = helpers.get_item(graph, path=args.path[0].replace('\\','/'))
        driveitem = DriveItem.from_json(item)
        
        print(f"Deleting {driveitem.name}...")

        helpers.delete_item(graph, item_id=driveitem.id)

        print(f"Done")

        return Success()
