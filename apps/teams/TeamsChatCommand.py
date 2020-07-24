from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.SampleModel import SampleModel
from models.User import User
from models.ChatMessage import ChatMessage
from models.ChatThread import ChatThread
from argparse import Namespace
from sqlalchemy import func, distinct
from apps.teams.TeamsCacheCommand import TeamsCacheCommand
import curses
from curses.textpad import Textbox, rectangle
from time import sleep



class TeamsChatCommand(BaseCommand):
    def add_parser(self, subparsers):
        chat_cmd = subparsers.add_parser(
            "chat", description="This is the teams chat UI"
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

        # TODO: Figure out how to specify the user / thread
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

        query_string = f"%{username}%"
        users = db.session.query(User)
        users_like = users.filter(User.display_name.ilike(query_string)).union(
            users.filter(User.mail.ilike(query_string))
        )
        # [print(f'{u.display_name}') for u in users_like.all()]
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

        messages = target_thread.messages.order_by(ChatMessage.created_date_time).all()

        txt = [
            f"\x1b[90m@{msg.sender.display_name}\x1b[m: {msg.body}" for msg in messages
        ]
        [print(m) for m in txt]

        self.do_chat_ui(instance, target_thread, matched_user)

        return Success()



    def do_chat_ui(self, instance, thread, other_user):
        def main(stdscr):
            curses.use_default_colors()
            # Clear screen
            stdscr.clear()

            TITLE_COLOR = 1
            USERNAME_COLOR = 2
            DATETIME_COLOR = 3

            curses.init_color(TITLE_COLOR, curses.COLOR_WHITE, curses.COLOR_MAGENTA)
            curses.init_pair(USERNAME_COLOR, curses.COLOR_BLACK, -1)
            curses.init_pair(DATETIME_COLOR, curses.COLOR_BLACK, -1)

            title = f'chatting with {other_user.display_name}' if other_user else 'group...'
            # stdscr.addstr(0, 0, title, curses.A_REVERSE)
            stdscr.addstr(0, 0, title, curses.color_pair(TITLE_COLOR))

            stdscr.refresh()
            # # This raises ZeroDivisionError when i == 10.
            # for i in range(0, 9):
            #     v = i-10
            #     sleep(.5)
            #     stdscr.addstr(i, 0, '10 divided by {} is {}'.format(v, 10/v))
            #     stdscr.refresh()

            # stdscr.getkey()

            # Your application can determine the size of the screen by using the
            # curses.LINES and curses.COLS variables to obtain the y and x
            # sizes. Legal coordinates will then extend from (0,0) to
            # (curses.LINES - 1, curses.COLS - 1).
            window_width = curses.COLS - 1
            window_height = curses.LINES - 1

            pad = curses.newpad(100, window_width)


            messages = thread.messages.order_by(ChatMessage.created_date_time).all()
            curr_row = 0
            for msg in messages:
                username = f'@{msg.sender.display_name}: '
                pad.addstr(curr_row, 0, username, curses.color_pair(USERNAME_COLOR))
                pad.addstr(curr_row, len(username), f'{msg.body}')
                curr_row+=1
            # txt = [
            #     f"\x1b[90m@{msg.sender.display_name}\x1b[m: {msg.body}" for msg in messages
            # ]
            # [print(m) for m in txt]

            # # These loops fill the pad with letters; addch() is
            # # explained in the next section
            # for y in range(0, 99):
            #     for x in range(0, 99):
            #         pad.addch(y,x, ord('a') + (x*x+y*y) % 26)

            # Displays a section of the pad in the middle of the screen.
            # (0,0) : coordinate of upper-left corner of pad area to display.
            # (5,5) : coordinate of upper-left corner of window area to be filled
            #         with pad content.
            # (20, 75) : coordinate of lower-right corner of window area to be
            #          : filled with pad content.
            # pad.refresh( 0,0, 5,5, 20,75)
            pad.refresh( 0,0, 1,0, window_height,window_width)

            stdscr.refresh()

            exit_requested = False
            while not exit_requested:
                k = stdscr.getkey()
                if k == '\x03':
                    exit_requested = True

        curses.wrapper(main)


