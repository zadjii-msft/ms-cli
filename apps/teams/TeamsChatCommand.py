from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.SampleModel import SampleModel
from models.User import User
from models.ChatMessage import ChatMessage
from models.ChatThread import ChatThread
from argparse import Namespace
from sqlalchemy import func, distinct

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

        target_thread = None

        all_threads = db.session.query(ChatThread)
        for t in all_threads.all():
            thread_messages = t.messages
            # I don't understanc this, but this will get us a list of users
            # comprised of all the senders of messages in the thread
            subq = thread_messages.subquery()
            thread_senders =  db.session.query(User).join(subq, User.guid == subq.c.from_guid)
            # sender_names = [s.display_name for s in thread_senders.all()]
            # print(f'{sender_names}')
            # all_senders = thread_senders.all()
            has_me = thread_senders.filter(User.id == current_user.id).count() > 0
            has_other = True
            # DO NOT USE .count() for this:
            # is_two_people = thread_senders.count() == 2
            # see https://docs.sqlalchemy.org/en/13/orm/query.html#sqlalchemy.orm.query.Query
            is_two_people = len(thread_senders.all()) == 2
            if has_me and has_other and is_two_people:
                print('found target_thread')
                target_thread = t
            # else:
            #     print(f'thread did not match, {has_me}, {has_other}, {senders_in_thread}, {is_two_people}')


        if target_thread is None:
            return Error(f'Could not find a thread for user:{username}')

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

        # sent_chat_messages = current_user.sent_chat_messages.all()
        messages = target_thread.messages.order_by(ChatMessage.created_date_time).all()

        txt = [
            f"\x1b[90m@{msg.sender.display_name}\x1b[m: {msg.body}"
            for msg in messages
        ]
        [print(m) for m in txt]

        return Success()
