from common.CaughtParserError import CaughtParserError
from common.ResultAndData import *
import sys
import common.ParserState


def do_common_interactive_with_args(modename, parser, instance, args):
    common.ParserState.doExitOnError = False

    extraHelp = "Navigation commands include: 'up' or 'back' to go up one menu level and 'quit' or 'exit' to leave completely."

    while True:
        print(f"ms {modename}>", end=" ")
        command = input().split(" ")

        if len(command) == 1:
            c = command[0].lower()

            if c == "help":
                parser.print_apps_help()
                print(extraHelp)
                continue

            if c == "exit" or c == "quit":
                print("Goodbye")
                sys.exit(0)

            if c == "up" or c == "back":
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
            print(extraHelp)

    return Error()
