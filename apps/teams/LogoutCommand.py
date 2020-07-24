from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.SampleModel import SampleModel
from models.User import User, get_or_create_user_model
from models.ChatMessage import ChatMessage, get_or_create_message_model
from models.ChatThread import ChatThread, get_or_create_thread_model
from argparse import Namespace
from msgraph import helpers
import json
import os


class LogoutCommand(BaseCommand):
    def add_parser(self, subparsers):
        logout_cmd = subparsers.add_parser(
            "logout", description="log out of the Microsoft Graph"
        )
        return logout_cmd

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData
        ms_cli_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        os.remove(os.path.join(ms_cli_root, 'microsoft.bin'))
        return Success()
