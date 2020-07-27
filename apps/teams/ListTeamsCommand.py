from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.SampleModel import SampleModel
from models.User import User, get_or_create_user_model
from models.ChatMessage import ChatMessage, get_or_create_message_model
from models.ChatThread import ChatThread, get_or_create_thread_model
from models.Team import Team, get_or_create_team_model
from argparse import Namespace
from msgraph import helpers
import json


class ListTeamsCommand(BaseCommand):
    def add_parser(self, subparsers):
        list_cmd = subparsers.add_parser("list", description="list all your teams")
        return list_cmd

    @staticmethod
    def cache_all_teams(instance, quiet=False):
        # type: (Instance) -> ResultAndData
        db = instance.get_db()
        graph = instance.get_graph_session()

        teams = helpers.list_joined_teams(graph)["value"]
        for team_json in teams:
            team = get_or_create_team_model(db, team_json)

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData

        instance.login_to_graph()
        db = instance.get_db()
        graph = instance.get_graph_session()

        ListTeamsCommand.cache_all_teams(instance, True)

        for team in db.session.query(Team).all():
            print(team.display_name)
