from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.SampleModel import SampleModel
from models.User import User
from models.ChatMessage import ChatMessage, get_or_create_message_model
from models.ChatThread import ChatThread, get_or_create_thread_model
from argparse import Namespace
from sqlalchemy import func, distinct
from apps.teams.TeamsCacheCommand import TeamsCacheCommand
import curses
from curses.textpad import Textbox, rectangle
from time import sleep
from msgraph import helpers


class ChatUI(object):

    TITLE_COLOR = 1
    USERNAME_COLOR = 2
    DATETIME_COLOR = 3
    FOCUSED_INPUT_COLOR = 4
    UNFOCUSED_INPUT_COLOR = 5
    KEYBINDING_COLOR = 6

    def __init__(self, instance, thread, other_user):
        self.instance = instance
        self.thread = thread
        self.other_user = other_user
        self.current_user = instance.get_current_user().data

        self.stdscr = None
        self.editwin = None
        self.pad = None
        self.input_line = ""

        self.window_width = -1
        self.window_height = -1
        self._raw_title = (
            f"chatting with {self.other_user.display_name}"
            if self.other_user
            else "group..."
        )
        self.title = ""
        self.prompt = ""
        self.keybinding_labels = ""

        self.title_height = 1

        self.message_box_height = -1
        self.message_box_width = -1
        self.msg_box_origin_row = -1
        self.msg_box_origin_col = -1
        self.chat_history_height = -1

        self.keybinding_labels_height = -1
        self.keybinding_labels_width = -1
        self.keybinding_labels_origin_row = -1
        self.keybinding_labels_origin_col = -1

    def setup_curses(self):
        curses.use_default_colors()
        # Clear screen
        self.stdscr.clear()

        curses.init_pair(ChatUI.TITLE_COLOR, curses.COLOR_WHITE, curses.COLOR_MAGENTA)
        curses.init_pair(ChatUI.USERNAME_COLOR, curses.COLOR_BLACK, -1)
        curses.init_pair(ChatUI.DATETIME_COLOR, curses.COLOR_BLACK, -1)
        curses.init_pair(ChatUI.FOCUSED_INPUT_COLOR, -1, -1)
        curses.init_pair(
            ChatUI.UNFOCUSED_INPUT_COLOR, curses.COLOR_BLACK, curses.COLOR_WHITE
        )
        curses.init_pair(ChatUI.KEYBINDING_COLOR, curses.COLOR_WHITE, -1)

        self.prompt = "Enter a message:"
        self.keybinding_labels = "| ^C: exit | ^Enter: send | ^R: Refresh messages |"
        self.update_sizes()

    def update_sizes(self):

        self.window_width = curses.COLS - 1
        self.window_height = curses.LINES - 1

        self.title_height = 1
        self.title = self._raw_title + (
            " " * (self.window_width - len(self._raw_title))
        )

        self.message_box_height = 2
        self.message_box_width = self.window_width - len(self.prompt) - 2
        self.msg_box_origin_row = self.window_height - self.message_box_height
        self.msg_box_origin_col = len(self.prompt) + 1

        self.keybinding_labels_height = 1
        self.keybinding_labels_width = self.window_width
        self.keybinding_labels_origin_row = self.window_height
        self.keybinding_labels_origin_col = 0

        self.chat_history_height = self.window_height - (
            self.message_box_height + self.title_height + self.keybinding_labels_height
        )

    @staticmethod
    def main(stdscr, self):
        self.stdscr = stdscr
        self.setup_curses()

        stdscr.addstr(0, 0, self.title, curses.color_pair(ChatUI.TITLE_COLOR))
        stdscr.addstr(
            self.keybinding_labels_origin_row,
            self.keybinding_labels_origin_col,
            self.keybinding_labels,
            curses.color_pair(ChatUI.KEYBINDING_COLOR),
        )

        # editwin = curses.newwin(height, width, y, x)
        self.editwin = curses.newwin(
            self.message_box_height,
            self.message_box_width,
            self.msg_box_origin_row,
            self.msg_box_origin_col,
        )
        self.editwin.bkgd(" ", curses.color_pair(ChatUI.UNFOCUSED_INPUT_COLOR))

        self.stdscr.addstr(self.msg_box_origin_row, 0, self.prompt)
        self.stdscr.refresh()

        self.pad = curses.newpad(100, self.window_width)

        self.draw_messages()

        def refresh_display(self):
            new_cursor_row = self.msg_box_origin_row + 0
            new_cursor_col = self.msg_box_origin_col + len(self.input_line)
            # msg_box_origin_col
            # editwin.move(0, len(input_line))
            stdscr.move(new_cursor_row, new_cursor_col)

            self.stdscr.refresh()
            self.editwin.refresh()

            # Displays a section of the pad in the middle of the screen.
            # (0,0) : coordinate of upper-left corner of pad area to display.
            # (5,5) : coordinate of upper-left corner of window area to be filled
            #         with pad content.
            # (20, 75) : coordinate of lower-right corner of window area to be
            #          : filled with pad content.
            # pad.refresh( 0,0, 5,5, 20,75)
            self.pad.refresh(0, 0, 1, 0, self.chat_history_height, self.window_width)

        refresh_display(self)

        exit_requested = False
        while not exit_requested:
            k = stdscr.getkey()
            if k == "\x03":
                exit_requested = True
            elif k == "CTL_ENTER":  # normal enter is '\n'
                if self.input_line == None or self.input_line == "":
                    pass
                else:
                    self.send_message(self.input_line)
                self.input_line = ""
                self.editwin.clear()
                self.draw_messages()
                refresh_display(self)
                refresh_display(self)
            elif k == "\n":
                pass
            elif k == "\x12":  # ^R
                TeamsCacheCommand.cache_all_messages(self.instance, quiet=True)
                self.draw_messages()
                refresh_display(self)
                refresh_display(self)
            elif k == "\x08":
                self.input_line = self.input_line[:-1]
                self.editwin.clear()
                self.editwin.addstr(0, 0, self.input_line)
                refresh_display(self)
                refresh_display(self)
            else:
                self.input_line += k

                self.editwin.addstr(0, 0, self.input_line)
                refresh_display(self)
                refresh_display(self)

    def start(self):
        curses.wrapper(ChatUI.main, self)

    def draw_messages(self):
        messages = self.thread.messages.order_by(ChatMessage.created_date_time).all()
        curr_row = 0
        for msg in messages:
            username = f"{msg.sender.display_name}: "
            self.pad.addstr(
                curr_row, 0, username, curses.color_pair(ChatUI.USERNAME_COLOR)
            )
            self.pad.addstr(curr_row, len(username), f"{msg.body}")
            curr_row += 1
        if len(messages) == 0:
            self.pad.addstr(
                curr_row,
                len(username),
                f"starting a new conversation with {msg.sender.display_name}",
            )
            curr_row += 1

    def send_message(self, message):
        db = self.instance.get_db()
        graph = self.instance.get_graph_session()
        response = helpers.send_chat_message(
            graph, chat_id=self.thread.graph_id, message=message
        )
        resp_json = response.json()

        msg_model = get_or_create_message_model(db, resp_json)
        msg_model.thread_id = self.thread.id
        msg_model.from_id = self.current_user.id
        db.session.commit()


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

        # Figure out who the user / thread is by display name or username
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
        # This will get us the first user who's display_name or email contains
        # the given string.
        query_string = f"%{username}%"
        users = db.session.query(User)
        users_like = users.filter(User.display_name.ilike(query_string)).union(
            users.filter(User.mail.ilike(query_string))
        )
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

        chat_ui = ChatUI(instance, target_thread, matched_user)
        chat_ui.start()

        return Success()
