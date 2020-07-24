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

        username = args.user
        print(f"chatting with {username}")

        db = instance.get_db()
        instance.login_to_graph()

        rd = instance.get_current_user()
        if not rd.success:
            return Error("no logged in user")
        current_user = rd.data

        # TODO: Figure out how to specify the user / thread
        #
        # We probably want
        #   `ms teams chat miniksa`
        # and
        #  `ms teams chat "Michael Niksa"`
        #
        # to get the same thread. The trick is, a thread doesn't necessarily
        # have two participants. How do we get all the participants of a thread?
        # And how do we find just the thread with the two of us?
        #

        # other_user = db.session.query(User).filter_by(name=username).first()
        # if other_user is None:
        #     print(f"Couldn't find user {username}")
        #     return Error()

        # Get all the messages either from us to them, or from the other user to us
        # messages_from_current = (
        #     db.session.query(ChatMessage)
        #     .filter(ChatMessage.sender_id == current_user.id)
        #     .filter(ChatMessage.target_id == other_user.id)
        # )
        #
        # messages_from_other = (
        #     db.session.query(ChatMessage)
        #     .filter(ChatMessage.sender_id == other_user.id)
        #     .filter(ChatMessage.target_id == current_user.id)
        # )
        #
        # # combine them, and get the results
        # messages = messages_from_current.union(messages_from_other).all()

        sent_chat_messages = current_user.sent_chat_messages.all()

        txt = [
            f"\x1b[90m@{msg.sender.display_name}\x1b[m: {msg.body}"
            for msg in sent_chat_messages
        ]
        [print(m) for m in txt]

        return Success()
