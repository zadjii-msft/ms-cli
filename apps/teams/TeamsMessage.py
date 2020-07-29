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
from apps.teams.ChatUI import ChatUI
from apps.teams.TeamsCacheCommand import TeamsCacheCommand
from apps.teams.ListTeamsCommand import ListTeamsCommand
from apps.teams.TeamsTeamCommand import TeamsTeamCommand


class TeamsMessage(BaseCommand):
    def add_parser(self, subparsers):
        message_cmd = subparsers.add_parser(
            "message", description="Open a specific chat message"
        )

        message_cmd.add_argument("message_id", help="The message to jump to")

        return message_cmd

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData

        instance.login_to_graph()
        db = instance.get_db()
        graph = instance.get_graph_session()

        msg = (
            db.session.query(ChatMessage)
            .filter(ChatMessage.graph_id == args.message_id)
            .first()
        )
        if msg is None:
            return Error("No matching message found")

        # Determine the message type
        if not msg.is_channel_message():
            # it's a DM
            #
            # TODO: Figure out the name for the thread. For threads with just
            # one other user, it should be their name. For groups, does the API
            # give us a way to get the thread's name? or is it just "user1,
            # user2, and 4 others"
            ui = ChatUI.create_for_direct_message(
                instance, msg.thread, "an unknown user"
            )
        else:
            # It's a thread message. We should jump into that thread
            ui = ChatUI.create_for_channel_thread(instance, msg.channel, msg.parent)

        ui.skip_to_message(msg)
        ui.start()
        # open the chat UI jumped straight to that message

        return Success()
