from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.SampleModel import SampleModel
from models.User import User
from models.Team import Team
from models.Channel import Channel
from models.ChatMessage import ChatMessage, get_or_create_message_model
from models.ChatThread import ChatThread, get_or_create_thread_model
from argparse import Namespace
from sqlalchemy import func, distinct
from apps.teams.TeamsCacheCommand import TeamsCacheCommand
from apps.teams.ChatUI import ChatUI
import curses
import os
from curses.textpad import Textbox, rectangle
from time import sleep
from msgraph import helpers


class TeamChatCommand(BaseCommand):
    def add_parser(self, subparsers):
        chat_cmd = subparsers.add_parser(
            "channel", description="This is the teams chat UI"
        )

        chat_cmd.add_argument(
            "channel",
            help="The channel within a team to chat with. Should be in team/channel format",
        )
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

        channel_arg = args.channel

        rd = instance.get_current_user()
        if not rd.success:
            return Error("no logged in user")
        current_user = rd.data

        if not channel_arg or not "/" in channel_arg:
            return Error('Channel should be provided in "team/channel" format')

        parts = channel_arg.split("/")
        team_name = parts[0]
        channel_name = parts[1]

        teams = db.session.query(Team)
        teams_like = teams.filter(Team.display_name.ilike(f"%{team_name}%"))

        matched_team = teams_like.first()
        if matched_team is None:
            return Error(f"Could not find the team:{team_name}")

        channels_like = matched_team.channels.filter(
            Channel.display_name.ilike(f"%{channel_name}%")
        )
        matched_channel = channels_like.first()
        if matched_channel is None:
            return Error(f"Could not find the channel:{channel_name}")

        print(
            f"opening channel {matched_team.display_name}/{matched_channel.display_name}"
        )

        ui = ChatUI.create_for_channel(instance, matched_channel)
        ui.start()
        # for msg in matched_channel.messages:
        #     if msg.is_toplevel():
        #         print(f"@{msg.sender.display_name}: {msg.body}")
        #         replies = msg.replies.all()
        #         for reply in replies:
        #             print(f"\t@{reply.sender.display_name}: {reply.body}")
