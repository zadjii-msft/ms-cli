from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.DriveItem import DriveItem
import argparse
from argparse import Namespace
from msgraph import helpers
import requests
import os


class OnedriveMakeDirCommand(BaseCommand):
    def add_parser(self, subparsers):
        list_cmd = subparsers.add_parser(
            "mkdir", description="Makes a subdirectory in one drive"
        )

        list_cmd.add_argument("name", help="new name for the item")
        list_cmd.add_argument(
            "path", help="path to the parent folder", nargs=argparse.REMAINDER
        )

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

        if len(args.path) > 1:
            return Error("Too many paths")

        newitemname = args.name

        if args.path:
            parentpath = args.paths
            print(f"Creating directory {newitemname} under {parentpath}...")
            helpers.make_folder(graph, foldername=newitemname, parent=parentpath)
        else:
            print(f"Creating directory {newitemname} at root...")
            helpers.make_folder(graph, foldername=newitemname)

        print(f"Done")

        return Success()
