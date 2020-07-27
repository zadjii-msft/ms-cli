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

        self.stdscr.addstr(0, 0, self.title, curses.color_pair(ChatUI.TITLE_COLOR))
        self.stdscr.addstr(
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

        self.refresh_display()

        exit_requested = False
        while not exit_requested:
            k = self.stdscr.getkey()
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
                self.refresh_display()
                self.refresh_display()
            elif k == "\n":
                pass
            elif k == "\x12":  # ^R
                TeamsCacheCommand.cache_all_messages(self.instance, quiet=True)
                self.draw_messages()
                self.refresh_display()
                self.refresh_display()
            elif k == "\x08":
                self.input_line = self.input_line[:-1]
                self.editwin.clear()
                self.editwin.addstr(0, 0, self.input_line)
                self.refresh_display()
                self.refresh_display()
            else:
                self.input_line += k

                self.editwin.addstr(0, 0, self.input_line)
                self.refresh_display()
                self.refresh_display()

    def start(self):
        curses.wrapper(ChatUI.main, self)

    def refresh_display(self):
        new_cursor_row = self.msg_box_origin_row + 0
        new_cursor_col = self.msg_box_origin_col + len(self.input_line)
        # msg_box_origin_col
        # editwin.move(0, len(input_line))
        self.stdscr.move(new_cursor_row, new_cursor_col)

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
