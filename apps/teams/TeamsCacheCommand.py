from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.SampleModel import SampleModel
from models.User import User, get_or_create_user_model
from models.ChatMessage import ChatMessage, get_or_create_message_model
from models.ChatThread import ChatThread, get_or_create_thread_model
from argparse import Namespace
from msgraph import helpers
import json


class TeamsCacheCommand(BaseCommand):
    def add_parser(self, subparsers):
        cache_cmd = subparsers.add_parser(
            "cache", description="cache all direct chat threads from Teams"
        )
        return cache_cmd

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData

        instance.login_to_graph()

        return TeamsCacheCommand.cache_all_messages(instance)

    @staticmethod
    def cache_all_messages(instance, quiet=False):
        # type: (Instance) -> ResultAndData
        db = instance.get_db()
        graph = instance.get_graph_session()

        if not quiet:
            print(f"fetching all messages...")

        chats = helpers.list_chats(graph)

        all_thread_ids = []
        for chat in chats["value"]:
            thread = get_or_create_thread_model(db, chat)
            all_thread_ids.append(thread.graph_id)
        for thread_guid in all_thread_ids:
            thread = (
                db.session.query(ChatThread)
                .filter(ChatThread.graph_id == thread_guid)
                .first()
            )
            if thread is None:
                return Error(f"the chat thread should never be None here")

            messages = helpers.list_chat_messages(graph, chat_id=thread_guid)

            for msg_json in messages["value"]:
                msg_model = get_or_create_message_model(db, msg_json)
                msg_model.thread_id = thread.id

                from_id = msg_json["from"]["user"]["id"]
                # Make sure user {from_id} is in the db
                user_json = helpers.get_user(graph, user_id=from_id)
                sender = get_or_create_user_model(db, user_json)
                msg_model.from_id = sender.id
                db.session.commit()

        return Success()
