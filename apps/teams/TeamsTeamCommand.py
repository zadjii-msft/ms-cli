from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.SampleModel import SampleModel
from models.User import User, get_or_create_user_model
from models.Team import Team, get_or_create_team_model
from models.Channel import Team, get_or_create_channel_model
from models.ChatMessage import ChatMessage, get_or_create_message_model
from models.ChatThread import ChatThread, get_or_create_thread_model
from apps.teams.ListTeamsCommand import ListTeamsCommand
from argparse import Namespace
from msgraph import helpers
import json


class TeamsTeamCommand(BaseCommand):
    def add_parser(self, subparsers):
        team_cmd = subparsers.add_parser("team", description="Interact with a team")
        team_cmd.add_argument("team", help="The team to interact with")
        team_cmd.add_argument(
            "--no-cache",
            action="store_true",
            help="if passed, disable caching on launch",
        )
        return team_cmd

    @staticmethod
    def cache_all_channels(instance, team, quiet=False):
        # type: (Instance) -> ResultAndData
        db = instance.get_db()
        graph = instance.get_graph_session()

        channels = team.get_channels_json(graph)
        for channel_json in channels["value"]:
            c = get_or_create_channel_model(db, channel_json)
            c.team_id = team.graph_id

        db.session.commit()

    @staticmethod
    def cache_messages_in_channel(instance, channel, quiet=False):
        # type: (Instance) -> ResultAndData
        db = instance.get_db()
        graph = instance.get_graph_session()
        team = channel.team

        response = helpers.list_channel_messages(
            graph, team_id=team.graph_id, channel_id=channel.graph_id
        )
        for chat_json in response["value"]:
            msg = get_or_create_message_model(db, chat_json)

            chat_id = chat_json["id"]

            replies = helpers.list_channel_message_replies(
                graph,
                team_id=team.graph_id,
                channel_id=channel.graph_id,
                chat_id=msg.graph_id,
            )
            for reply_json in replies["value"]:
                reply = get_or_create_message_model(db, reply_json)

        db.session.commit()

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData

        instance.login_to_graph()
        db = instance.get_db()
        graph = instance.get_graph_session()

        if not args.no_cache:
            ListTeamsCommand.cache_all_teams(instance)

        team_name = args.team
        query_string = f"%{team_name}%"

        teams = db.session.query(Team)
        teams_like = teams.filter(Team.display_name.ilike(query_string))

        matched_team = teams_like.first()
        if matched_team is None:
            return Error(f"Could not find the team:{team_name}")

        # channels = matched_team.get_channels_json(graph)
        # for channel_json in channels['value']:
        # print(json.dumps(channels, indent=2))
        #
        #     print('='*80)
        #     response = helpers.list_channel_messages(graph, team_id=matched_team.graph_id, channel_id=channel_json['id'])
        #     print(json.dumps(response, indent=2))
        #     for chat_json in response['value']:
        #         print('-'*80)
        #         chat_id = chat_json['id']
        #         chat_body = chat_json['body']['content']
        #         print(f'{chat_id} - {chat_body}')
        #         replies = helpers.list_channel_message_replies(graph, team_id=matched_team.graph_id, channel_id=channel_json['id'], chat_id=chat_id)
        #         print(json.dumps(replies, indent=2))
        #         print('-'*80)
        #     # print(response)

        TeamsTeamCommand.cache_all_channels(instance, matched_team)
        channels = matched_team.channels.all()
        # for chan in channels:
        #     print("=" * 80)
        #     response = helpers.list_channel_messages(
        #         graph, team_id=matched_team.graph_id, channel_id=chan.graph_id
        #     )
        #     print(json.dumps(response, indent=2))
        #     for chat_json in response["value"]:
        #         print("-" * 80)
        #         chat_id = chat_json["id"]
        #         chat_body = chat_json["body"]["content"]
        #         print(f"{chat_id} - {chat_body}")
        #         replies = helpers.list_channel_message_replies(
        #             graph,
        #             team_id=matched_team.graph_id,
        #             channel_id=chan.graph_id,
        #             chat_id=chat_id,
        #         )
        #         print(json.dumps(replies, indent=2))
        #         print("-" * 80)

        for chan in channels:
            TeamsTeamCommand.cache_messages_in_channel(instance, chan)

        for chan in channels:
            print("=" * 80)
            print(f"{chan.display_name}")
            print("=" * 80)
            for msg in chan.messages:
                if msg.is_toplevel():
                    print(f"@{msg.sender.display_name}: {msg.body}")
                    replies = msg.replies.all()
                    for reply in replies:
                        print(f"\t@{reply.sender.display_name}: {reply.body}")
