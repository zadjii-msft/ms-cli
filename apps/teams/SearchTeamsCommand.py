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
from apps.teams.TeamsCacheCommand import TeamsCacheCommand
from apps.teams.ListTeamsCommand import ListTeamsCommand
from apps.teams.TeamsTeamCommand import TeamsTeamCommand


class SearchTeamsCommand(BaseCommand):
    def add_parser(self, subparsers):
        search_cmd = subparsers.add_parser("search", description="Search your messages")

        search_cmd.add_argument(
            "query", help="The string to search for. Pass '*' to get all the messages."
        )

        search_cmd.add_argument(
            "--from",
            dest="from_user",
            help="If provided, search for messages only from the given user",
            default=None,
        )
        # search_cmd.add_argument("--user", help="TODO", default=None)
        search_cmd.add_argument(
            "--cache-chats",
            action="store_true",
            help="if passed, fetch chat messages before searching",
        )
        search_cmd.add_argument(
            "--cache-teams",
            action="store_true",
            help="if passed, fetch messages in team channels before searching",
        )
        search_cmd.add_argument(
            "--plain",
            action="store_true",
            help="Print each message as [id: {the message ID}] {the message text}. These results might be on multiple lines, if the message body contained newlines.",
        )

        return search_cmd

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData

        instance.login_to_graph()
        db = instance.get_db()
        graph = instance.get_graph_session()

        if args.cache_chats:
            TeamsCacheCommand.cache_all_messages(instance)
        if args.cache_teams:
            ListTeamsCommand.cache_all_teams(instance)
            for team in db.session.query(Team):
                TeamsTeamCommand.cache_all_channels(instance, team)
                for ch in team.channels:
                    TeamsTeamCommand.cache_messages_in_channel(instance, ch)

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
        if args.query == "*":
            # special case, just return all the results
            results = all_messages
        else:
            query_string = f"%{args.query}%"
            results = all_messages.filter(ChatMessage.body.ilike(query_string))

        if from_user:
            results = results.filter(ChatMessage.from_guid == from_user.guid)

        result_msgs = results.all()
        if len(result_msgs) == 0:
            return Error("No results found")

        if args.plain:
            self._print_plain(result_msgs)
        else:
            self._print_pretty(result_msgs)

        return Success()

    def _print_pretty(self, result_msgs):
        for i, msg in enumerate(result_msgs):
            (r, c) = os.get_terminal_size()
            # alternate BG colors
            background_format = (
                "\x1b[48;2;32;31;30m" if i % 2 == 0 else "\x1b[48;2;59;58;57m"
            )
            print(
                f'{background_format}id: {msg.graph_id} - {msg.created_date_time.strftime("%c")}\x1b[K\x1b[m'
            )
            print(f"\x1b[4;2m{msg.sender.display_name}:\x1b[24;22;39m {msg.body}\x1b[m")

    def _print_plain(self, result_msgs):
        for i, msg in enumerate(result_msgs):
            print(f"[id: {msg.graph_id}] {msg.body}")
