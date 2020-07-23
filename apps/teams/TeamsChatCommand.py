from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.SampleModel import SampleModel
from models.User import User
from models.ChatMessage import ChatMessage
from argparse import Namespace


class TeamsChatCommand(BaseCommand):
    def add_parser(self, subparsers):
        chat_cmd = subparsers.add_parser(
            "chat", description="This is the teams chat UI"
        )

        chat_cmd.add_argument("user", help="The user to chat with")

        return chat_cmd

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData

        # print("This is the teams chat command")
        username = args.user
        print(f"chatting with {username}")

        db = instance.get_db()

        rd = instance.get_current_user()
        if not rd.success:
            return Error('no logged in user')
        current_user = rd.data

        other_user = db.session.query(User).filter_by(name=username).first()
        if other_user is None:
            print(f"Couldn't find user {username}")
            return Error()

        # messages = db.session.query(ChatMessage).filter_by(sender_id=other_user.id).all()
        messages = db.session.query(ChatMessage).all()
        txt = [f"{msg.sender_id}->{msg.target_id}: {msg.content}" for msg in messages]
        print(txt)
        # print(f'{msg.sender_id}->{msg.target_id}: {msg.content}' for msg in messages)
        # messages = db.session.query(ChatMessage).filter(ChatMessage.sender_id==other_user.id).all()
        # messages = db.session.query(ChatMessage).filter(ChatMessage.target_id==other_user.id).all()
        # print(messages)

        return Success()
