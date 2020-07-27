from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.SampleModel import SampleModel
from models.User import User
from models.ChatMessage import ChatMessage, get_or_create_message_model
from models.ChatThread import ChatThread, get_or_create_thread_model
from argparse import Namespace
from sqlalchemy import func, distinct
from apps.teams.TeamsCacheCommand import TeamsCacheCommand
from apps.teams.ChatUI import ChatUI
import curses
from curses.textpad import Textbox, rectangle
from time import sleep
from msgraph import helpers


class DirectChatCommand(BaseCommand):
    def add_parser(self, subparsers):
        chat_cmd = subparsers.add_parser(
            "chat",
            description="This is the teams chat UI, for chatting with another user",
        )

        chat_cmd.add_argument("user", help="The user to chat with")
        chat_cmd.add_argument(
            "--no-cache",
            action="store_true",
            help="if passed, disable caching on launch",
        )

        return chat_cmd

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        db = instance.get_db()
        instance.login_to_graph()

        username = args.user

        rd = instance.get_current_user()
        if not rd.success:
            return Error("no logged in user")
        current_user = rd.data

        # Figure out who the user / thread is by display name or username
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
        # This will get us the first user who's display_name or email contains
        # the given string.
        query_string = f"%{username}%"
        users = db.session.query(User)
        users_like = users.filter(User.display_name.ilike(query_string)).union(
            users.filter(User.mail.ilike(query_string))
        )
        matched_user = users_like.first()
        if matched_user is None:
            return Error(f"Could not find the user:{username}")

        if not args.no_cache:
            TeamsCacheCommand.cache_all_messages(instance)

        print(f"chatting with {username}")

        target_thread = None

        all_threads = db.session.query(ChatThread)
        for t in all_threads.all():
            thread_messages = t.messages

            # I don't understanc this, but this will get us a list of users
            # comprised of all the senders of messages in the thread
            subq = thread_messages.subquery()
            thread_senders = db.session.query(User).join(
                subq, User.guid == subq.c.from_guid
            )

            has_me = thread_senders.filter(User.id == current_user.id).count() > 0
            has_other = thread_senders.filter(User.id == matched_user.id).count() > 0
            is_two_people = len(thread_senders.all()) == 2

            # DO NOT USE .count() for this:
            # is_two_people = thread_senders.count() == 2
            # see https://docs.sqlalchemy.org/en/13/orm/query.html#sqlalchemy.orm.query.Query
            if has_me and has_other and is_two_people:
                # print("found target_thread")
                target_thread = t
            # else:
            #     print(f'thread did not match, {has_me}, {has_other}, {senders_in_thread}, {is_two_people}')

        if target_thread is None:
            return Error(f"Could not find a thread for user:{username}")

        chat_ui = ChatUI.create_for_channel_thread(instance, target_thread, matched_user)
        chat_ui.start()

        return Success()
