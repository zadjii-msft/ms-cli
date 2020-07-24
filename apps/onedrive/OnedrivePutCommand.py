from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.DriveItem import DriveItem
import argparse
from argparse import Namespace
from msgraph import helpers
import requests
import os

class OnedrivePutCommand(BaseCommand):
    def add_parser(self, subparsers):
        list_cmd = subparsers.add_parser(
            "put", description="Puts an item into OneDrive"
        )

        list_cmd.add_argument('localPath', type=argparse.FileType('rb'))
        list_cmd.add_argument('remotePath', nargs=argparse.REMAINDER)
        
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

        if (len(args.remotePath) > 1):
            return Error("Too many paths")

        filename = args.localPath.name

        print(f"Uploading {filename}")

        helpers.upload_file_handle(graph, iterable=args.localPath, filename=filename)

        print(f"Done.")

        return Success()
