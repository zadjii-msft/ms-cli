from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.SampleModel import SampleModel
from models.User import User
from models.ChatMessage import ChatMessage
from models.ChatThread import ChatThread
from argparse import Namespace
from msgraph import helpers
import json


def get_or_create_thread_model(db, thread_json):
    # type: (SimpleDB, json) -> ChatThread

    id_from_json = thread_json["id"]
    thread = (
        db.session.query(ChatThread).filter(ChatThread.graph_id == id_from_json).first()
    )
    if thread is None:
        # print(f'found a new chat thread {id_from_json}')
        thread = ChatThread.from_json(thread_json)
        # print(f'Created a new thread {thread.__dict__}')
        db.session.add(thread)
        db.session.commit()
    return thread


def get_or_create_message_model(db, msg_json):
    # type: (SimpleDB, json) -> ChatMessage
    id_from_json = msg_json["id"]
    msg_model = (
        db.session.query(ChatMessage)
        .filter(ChatMessage.graph_id == id_from_json)
        .first()
    )
    if msg_model is None:
        msg_model = ChatMessage.from_json(msg_json)
        db.session.add(msg_model)
        db.session.commit()
    return msg_model


def get_or_create_user_model(db, user_json):
    # type: (SimpleDB, json) -> User
    id_from_json = user_json["id"]
    user_model = db.session.query(User).filter(User.guid == id_from_json).first()
    if user_model is None:
        user_model = User.from_json(user_json)
        db.session.add(user_model)
        db.session.commit()
    return user_model


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
        # print(json.dumps(chats, indent=2))

        all_thread_ids = []
        for chat in chats["value"]:
            thread = get_or_create_thread_model(db, chat)
            all_thread_ids.append(thread.graph_id)

        # print('All threads:')
        # [print(f'\t{thread.graph_id}') for thread in db.session.query(ChatThread).all()]

        # chat_id = chats["value"][0]["id"]

        # response = helpers.send_message(session, team_id=team_id, channel_id=chat_id, message="farts")
        # response = helpers.send_chat_message(
        #     session,
        #     chat_id=chat_id,
        #     message="hey michael this is a message mike using the tool",
        # )
        # print(response)
        for thread_guid in all_thread_ids:
            # print(f'looking for messages in thread:{thread_guid}')
            thread = (
                db.session.query(ChatThread)
                .filter(ChatThread.graph_id == thread_guid)
                .first()
            )
            if thread is None:
                return Error(f"the chat thread should never be None here")

            messages = helpers.list_chat_messages(graph, chat_id=thread_guid)
            # print(json.dumps(messages, indent=2))
            for msg_json in messages["value"]:
                print(msg_json)
                msg_model = get_or_create_message_model(db, msg_json)
                msg_model.thread_id = thread.id

                from_id = msg_json["from"]["user"]["id"]
                # print(f'Make sure user {from_id} is in the db...')
                user_json = helpers.get_user(graph, user_id=from_id)
                sender = get_or_create_user_model(db, user_json)
                msg_model.from_id = sender.id
                db.session.commit()

            # db.session.commit()

        # print(messages)
        # print(json.dumps(messages, indent=2))

        return Success()
