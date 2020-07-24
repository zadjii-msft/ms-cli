from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.DriveItem import DriveItem
import argparse
from argparse import Namespace
from msgraph import helpers
from tabulate import tabulate

class OnedriveListCommand(BaseCommand):
    def add_parser(self, subparsers):
        list_cmd = subparsers.add_parser(
            "ls", description="This is the onedrive list UI"
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

        if args.path:
            if (len(args.path) > 1):
                return Error("Too many paths")
            itemlist = helpers.list_folder(graph, parent=args.path[0].replace('\\','/'))
        else:
            itemlist = helpers.list_folder(graph)
        
        items = []
        for item in itemlist["value"]:
            driveItem = DriveItem.from_json(item)
            items.append(driveItem)


        table = []
        for i in items:
            q = [i.type, i.modified, i.size, i.name]
            table.append(q)
            
        print(tabulate(table, headers=["Type", "Last Modified", "Size", "Name"]))

        return Success()
