from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.SampleModel import SampleModel
from models.User import User
from models.ChatMessage import ChatMessage
from models.ChatThread import ChatThread
from argparse import Namespace
from msgraph import helpers
import json


class TeamsCacheCommand(BaseCommand):
    def add_parser(self, subparsers):
        cache_cmd = subparsers.add_parser(
            "cache", description="cache teams chat threads"
        )

        # cache_cmd.add_argument("user", help="The user to chat with")

        return cache_cmd

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData

        db = instance.get_db()
        instance.login_to_graph()
        graph = instance.get_graph_session()



        chats = helpers.list_chats(graph)
        # print(chats)
        print(json.dumps(chats, indent=2))

        all_thread_ids = []
        for chat in chats["value"]:
            id_from_json =chat['id']
            thread = db.session.query(ChatThread).filter(id == id_from_json).first()
            if thread is None:
                print(f'found a new chat thread {id_from_json}')
                thread = ChatThread.from_json(chat)
                db.session.add(thread)
            all_thread_ids.append(thread.graph_id)

        db.session.commit()



        chat_id = chats["value"][0]["id"]

        # response = helpers.send_message(session, team_id=team_id, channel_id=chat_id, message="farts")
        # response = helpers.send_chat_message(
        #     session,
        #     chat_id=chat_id,
        #     message="hey michael this is a message mike using the tool",
        # )
        # print(response)

        messages = helpers.list_chat_messages(graph, chat_id=chat_id)

        # print(messages)
        print(json.dumps(messages, indent=2))

        return Success()
