import abc
from argparse import Namespace
from common.ResultAndData import *


class BaseCommand(object):
    __metaclass__ = abc.ABCMeta
    """
    Abstracts out some boilerplate for adding a subcommand. Just define all the
    args in add_parser, and the implementation in do_command_with_args.
    """

    def __init__(self, subparsers):
        self._parser = self.add_parser(subparsers)
        self._parser.set_defaults(func=self.get_command())

    def get_command(self):
        return lambda instance, args: self.do_command_with_args(instance, args)

    @abc.abstractmethod
    def add_parser(self, subparsers):
        """
        Add this command to the given subparsers
        """
        return None

    @abc.abstractmethod
    def do_command_with_args(self, instance, args):
        # type: (Instance, Namespace) -> ResultAndData

        """
        Execute this command, with the Namespace as parsed by argparse.
        """
        return Error()


# A sample of how to use:
#
# from common.BaseCommand import BaseCommand
# from common_util import ResultAndData, Error, Success
# from argparse import Namespace
# class SampleCommand(BaseCommand):
#     def add_parser(self, subparsers):
#         sample = subparsers.add_parser('sample', description='sample')
#         return sample
#
#     def do_command_with_args(self, instance, args):
#         # type: (Instance, Namespace) -> ResultAndData
#         return Error()
