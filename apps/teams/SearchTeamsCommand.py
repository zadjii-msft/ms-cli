from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from common.utils import *
from models.SampleModel import SampleModel
from models.User import User, get_or_create_user_model
from models.ChatMessage import ChatMessage, get_or_create_message_model
from models.ChatThread import ChatThread, get_or_create_thread_model
from models.Team import Team, get_or_create_team_model
from argparse import Namespace
from msgraph import helpers
import json
import os


class SearchTeamsCommand(BaseCommand):
    def add_parser(self, subparsers):
        search_cmd = subparsers.add_parser("search", description="Search your messages")

        search_cmd.add_argument("query", help="The string to search for")

        search_cmd.add_argument("--from-user", help="TODO", default=None)
        search_cmd.add_argument("--user", help="TODO", default=None)
        search_cmd.add_argument(
            "--no-cache",
            action="store_true",
            help="if passed, disable caching on launch",
        )

        return search_cmd

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData

        instance.login_to_graph()
        db = instance.get_db()
        graph = instance.get_graph_session()

        from_user = None
        if args.from_user is not None:
            from_user_query_string = f"%{args.from_user}%"
            users = db.session.query(User)
            users_like = users.filter(
                User.display_name.ilike(from_user_query_string)
            ).union(users.filter(User.mail.ilike(from_user_query_string)))
            from_user = users_like.first()
            if from_user is None:
                return Error(f"Could not find the user:{args.from_user}")
            else:
                print(f"Searching messages from {from_user.display_name}")

        all_messages = db.session.query(ChatMessage).order_by(
            ChatMessage.created_date_time
        )
        query_string = f"%{args.query}%"
        results = all_messages.filter(ChatMessage.body.ilike(query_string))

        if from_user:
            results = results.filter(ChatMessage.from_guid == from_user.guid)

        result_msgs = results.all()
        if len(result_msgs) == 0:
            return Error("No results found")

        for msg in result_msgs:
            (r, c) = os.get_terminal_size()
            # print(f'\x1b[4m{" " * 32}\x1b[0m')
            # print(f'\x1b[48;2;32;31;30mid: {msg.graph_id} - {datetime_to_string(msg.created_date_time)}\x1b[K\x1b[m')
            print(
                f'\x1b[48;2;32;31;30mid: {msg.graph_id} - {msg.created_date_time.strftime("%c")}\x1b[K\x1b[m'
            )
            # print(f'\x1b[100mid: {msg.graph_id}\x1b[K\x1b[m')
            print(f"\x1b[4;2m{msg.sender.display_name}:\x1b[0m {msg.body}")
