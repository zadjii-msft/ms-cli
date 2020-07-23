from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from argparse import Namespace


class TeamsCommand(BaseCommand):
    def add_parser(self, subparsers):
        sample = subparsers.add_parser('teams', description='This is the teams application')
        return sample

    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData

        print('This is the teams command')
        return Error()
