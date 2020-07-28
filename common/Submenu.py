from common.CaughtParserError import CaughtParserError
from common.ResultAndData import *
import sys
import common.ParserState


def do_common_interactive_with_args(modename, parser, instance, args):
    common.ParserState.doExitOnError = False
    while True:
        print(f"ms {modename}>", end=" ")
        command = input().split(" ")

        if len(command) == 1:
            c = command[0].lower()

            if command[0].lower() == "exit" or command[0].lower() == "quit":
                print("Goodbye")
                sys.exit(0)

            if command[0].lower() == "up" or command[0].lower() == "back":
                print("Returning to main menu...")
                break

        try:
            args = parser.parse_args(args=command)

            if args.func:
                result = args.func(instance, args)
                if result is not None:
                    if not result.success:
                        if result.data:
                            print("\x1b[31m")
                            print(result.data)
                            print("\x1b[m")
            else:
                print("Invalid command")
        except CaughtParserError as e:
            print(e)

    return Error()
