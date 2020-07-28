from common.BaseCommand import BaseCommand
from common.ResultAndData import *
from models.SampleModel import SampleModel
from models.User import User
from models.ChatMessage import ChatMessage, get_or_create_message_model
from models.ChatThread import ChatThread, get_or_create_thread_model
from argparse import Namespace
from sqlalchemy import func, distinct
from apps.teams.TeamsCacheCommand import TeamsCacheCommand
from apps.teams.TeamsTeamCommand import TeamsTeamCommand
import curses
import os
from curses.textpad import Textbox, rectangle
from time import sleep
from msgraph import helpers


class EditBox(object):
    def __init__(self, width, contents=""):
        self._width = width
        self._buffer = contents
        self._caret_position = 0
        self._rows = None

    def resize(self, new_width):
        self._width = new_width
        self._rows = None

    def is_empty(self):
        return self._buffer is None or self._buffer == ""

    def get_contents(self):
        return self._buffer

    def clear(self):
        self._buffer = ""
        self._caret_position = 0
        self._rows = None

    def _at_buffer_end(self):
        return self._caret_position == len(self._buffer)

    def insert_character(self, ch):
        if self._at_buffer_end():
            self._buffer = self._buffer + ch
        else:
            self._buffer = (
                self._buffer[: self._caret_position]
                + ch
                + self._buffer[self._caret_position :]
            )
        self._caret_position += 1
        self._rows = None

    def backspace_character(self):
        if self._caret_position == 0:
            return
        elif self._at_buffer_end():
            self._buffer = self._buffer[:-1]
        else:
            self._buffer = (
                self._buffer[: self._caret_position - 1]
                + self._buffer[self._caret_position :]
            )
        self._caret_position -= 1
        self._clamp_caret()
        self._rows = None

    def delete_character(self):
        if self._at_buffer_end():
            return
        else:
            self._buffer = (
                self._buffer[: self._caret_position]
                + self._buffer[self._caret_position + 1 :]
            )
        self._clamp_caret()
        self._rows = None

    def move_cursor_left(self):
        self._caret_position -= 1
        self._clamp_caret()

    def move_cursor_right(self):
        self._caret_position += 1
        self._clamp_caret()

    def move_cursor_home(self):
        self._caret_position = 0
        self._clamp_caret()

    def move_cursor_end(self):
        self._caret_position = len(self._buffer)
        self._clamp_caret()

    def _clamp_caret(self):
        if self._caret_position < 0:
            self._caret_position = 0
        if self._caret_position >= len(self._buffer):
            self._caret_position = len(self._buffer)

    def get_rows(self):
        if self._rows is None:
            self._rows = [
                self._buffer[i : i + self._width]
                for i in range(0, len(self._buffer), self._width)
            ]
        return self._rows

    def get_height(self):
        rows = self.get_rows()
        return len(rows)

    def get_caret_xy(self):
        x = int(self._caret_position % self._width)
        y = int(self._caret_position / self._width)
        return (x, y)


class ChatUI(object):

    # UI Element colors. Use with curses.color_pair()
    TITLE_COLOR = 1
    USERNAME_COLOR = 2
    DATETIME_COLOR = 3
    FOCUSED_INPUT_COLOR = 4
    UNFOCUSED_INPUT_COLOR = 5
    KEYBINDING_COLOR = 6
    ACTIVE_THREAD_INDICATOR_COLOR = 7

    # Chat types
    INVALID = -1  # Uh oh! The ChatUI wasn't set up correctly!
    DIRECT_MESSAGE = 0  # A direct message with one other user
    GROUP_THREAD = 1  # A chat thread with many other users. Unimplemented
    CHANNEL_ROOT = 2  # A list of the threads in a channel in a team
    CHANNEL_MESSAGE = 3  # A single thread within a channel in a team

    @staticmethod
    def create_for_direct_message(instance, thread, other_user):
        # type: (Instance, ChatThread, User) -> ChatUI
        ui = ChatUI(instance)
        ui._mode = ChatUI.DIRECT_MESSAGE
        ui.thread = thread
        ui.other_user = other_user
        return ui

    @staticmethod
    def create_for_channel(instance, channel):
        # type: (Instance, Channel) -> ChatUI
        ui = ChatUI(instance)
        ui._mode = ChatUI.CHANNEL_ROOT
        ui._team = channel.team
        ui._channel = channel
        ui._selected_thread_index = 0
        return ui

    @staticmethod
    def create_for_channel_thread(instance, channel, root_message):
        # type: (Instance, Channel, ChatMessage) -> ChatUI
        ui = ChatUI(instance)
        ui._mode = ChatUI.CHANNEL_MESSAGE
        ui._team = channel.team
        ui._channel = channel
        ui._root_message = root_message
        ui._selected_thread_index = None
        return ui

    def __init__(self, instance):
        # type: (Instance) -> None
        self._mode = ChatUI.INVALID
        self.instance = instance
        self.thread = None
        self.other_user = None
        self.current_user = instance.get_current_user().data
        self._team = None
        self._channel = None
        self._root_message = None
        self._selected_thread_index = None
        self.exit_requested = False
        self._toplevel_messages = []

        self.stdscr = None
        self.editwin = None
        self.pad = None

        self._edit_box = EditBox(80)
        self._composing_new_thread = False

        self.window_width = -1
        self.window_height = -1
        self.title = ""
        self.prompt = ""
        # self.keybinding_labels = ""

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

    def open_thread(self, chat_message):
        self._mode = ChatUI.CHANNEL_MESSAGE
        self._root_message = chat_message
        self._toplevel_messages = []
        self._selected_thread_index = None
        self._redraw_everything()

    def _redraw_everything(self):
        self.setup_curses()
        self.draw_titlebar()
        self.draw_keybindings()
        self.draw_prompt()
        self.draw_edit_box()
        self.draw_messages()
        self.refresh_display()
        self.refresh_display()

    def setup_curses(self):
        curses.use_default_colors()

        ########################################################################
        # Setup colors to use with curses
        ########################################################################
        # See: https://docs.microsoft.com/en-us/microsoftteams/platform/concepts/design/components/color
        # The official Teams purple is #6264A7
        # We've got a few options for 256-palette colors:
        # * curses.COLOR_MAGENTA: this is the 16-color palette magenta.
        # * 093: #8700ff
        # * 099: #875fff
        # * 056: #5f00d7
        # * 062: #5f5fd7 - this is a little blue-er than the above one, but looks closer to my eyes
        curses.init_pair(ChatUI.TITLE_COLOR, curses.COLOR_WHITE, 62)
        curses.init_pair(ChatUI.USERNAME_COLOR, curses.COLOR_BLACK, -1)
        curses.init_pair(ChatUI.DATETIME_COLOR, curses.COLOR_BLACK, -1)
        curses.init_pair(
            ChatUI.FOCUSED_INPUT_COLOR, curses.COLOR_BLACK, curses.COLOR_WHITE
        )
        curses.init_pair(
            ChatUI.UNFOCUSED_INPUT_COLOR, curses.COLOR_WHITE, curses.COLOR_BLACK
        )
        curses.init_pair(ChatUI.KEYBINDING_COLOR, curses.COLOR_WHITE, -1)
        curses.init_pair(ChatUI.ACTIVE_THREAD_INDICATOR_COLOR, -1, curses.COLOR_WHITE)
        ########################################################################

        self.prompt = self._get_prompt()
        self.update_sizes()

    def update_sizes(self):
        # OKAY. Definitively, these guys are the right ones.
        #
        # GetConsoleScreenBufferInfo will return the size of the _main_
        # buffer, which _isn't_  resized till the buffer exits....
        curses.update_lines_cols()
        self.window_width = curses.COLS - 1
        self.window_height = curses.LINES - 1

        self.title_height = 1
        raw_title = self._get_raw_title()
        self.title = raw_title + (" " * (self.window_width - len(raw_title)))

        self.message_box_height = 2
        self.message_box_width = self.window_width - len(self.prompt) - 2
        self.msg_box_origin_row = self.window_height - self.message_box_height
        self.msg_box_origin_col = len(self.prompt) + 1
        self._edit_box.resize(self.message_box_width)

        self.keybinding_labels_height = 1
        self.keybinding_labels_width = self.window_width
        self.keybinding_labels_origin_row = self.window_height
        self.keybinding_labels_origin_col = 0

        self.chat_history_height = self.window_height - (
            self.message_box_height + self.title_height + self.keybinding_labels_height
        )

    def draw_titlebar(self):
        self.stdscr.addstr(0, 0, self.title, curses.color_pair(ChatUI.TITLE_COLOR))

    def _get_keybindings_labels(self):
        labels = "| ^C: exit | ^Enter: send | ^R: refresh |"
        if self._mode == ChatUI.CHANNEL_ROOT:
            if self._composing_new_thread:
                labels = "| ^C: exit | ^Enter: send | ^R: refresh | Esc: cancel |"
            else:
                labels = "| ^C: exit | Enter: open  | ^R: refresh | ^N: new thread | ↑↓: select thread |"
        else:
            pass

        return labels

    def draw_keybindings(self):
        self.stdscr.move(
            self.keybinding_labels_origin_row, self.keybinding_labels_origin_col
        )
        self.stdscr.clrtoeol()
        self.stdscr.addstr(
            self.keybinding_labels_origin_row,
            self.keybinding_labels_origin_col,
            self._get_keybindings_labels(),
            curses.color_pair(ChatUI.KEYBINDING_COLOR),
        )

    def draw_prompt(self):
        self.stdscr.addstr(self.msg_box_origin_row, 0, self.prompt)

    def draw_edit_box(self):
        attr = curses.color_pair(ChatUI.FOCUSED_INPUT_COLOR)
        if self._mode == ChatUI.CHANNEL_ROOT and not self._composing_new_thread:
            attr = curses.color_pair(ChatUI.UNFOCUSED_INPUT_COLOR)
            curses.curs_set(0)  # hide the cursor
        else:
            curses.curs_set(1)  # show the cursor

        self.editwin.bkgd(" ", attr)

        self.editwin.clear()

        for row_index, row_text in enumerate(self._edit_box.get_rows()):
            self.editwin.addstr(row_index, 0, row_text)

    @staticmethod
    def main(stdscr, self):
        self.stdscr = stdscr
        self.setup_curses()

        self.draw_titlebar()
        self.draw_keybindings()

        self.editwin = curses.newwin(
            self.message_box_height,
            self.message_box_width,
            self.msg_box_origin_row,
            self.msg_box_origin_col,
        )
        self.draw_edit_box()

        self.draw_prompt()
        self.stdscr.refresh()

        self.pad = curses.newpad(100, self.window_width)

        self.draw_messages()

        self.refresh_display()

        self.exit_requested = False
        while not self.exit_requested:
            k = self.stdscr.getkey()
            self._handle_key(k)

    def _handle_key(self, k):
        handled = False

        # Handle window resizing. Do this first
        if k == "KEY_RESIZE":
            self.update_sizes()
            self._redraw_everything()
            return True

        if self._mode == ChatUI.DIRECT_MESSAGE:
            pass
        elif self._mode == ChatUI.GROUP_THREAD:
            pass
        elif self._mode == ChatUI.CHANNEL_ROOT:
            handled = self._channel_handle_key(k)
        elif self._mode == ChatUI.CHANNEL_MESSAGE:
            pass
        if not handled:
            handled = self._base_handle_key(k)

    def _channel_handle_key(self, k):
        handled = False
        if k == "\n":
            self.open_thread(self._toplevel_messages[self._selected_thread_index])
            handled = True
        elif k == "KEY_A2" or k == "KEY_UP":  # UP
            if self._composing_new_thread:
                pass
            else:
                self._selected_thread_index = self._selected_thread_index - 1
                if self._selected_thread_index < 0:
                    self._selected_thread_index = 0
                self.draw_messages()
                self.refresh_display()
                handled = True
        elif k == "KEY_C2" or k == "KEY_DOWN":  # DOWN
            if self._composing_new_thread:
                pass
            else:
                self._selected_thread_index = self._selected_thread_index + 1
                if self._selected_thread_index >= len(self._toplevel_messages):
                    self._selected_thread_index = len(self._toplevel_messages) - 1
                self.draw_messages()
                handled = True
                self.refresh_display()
        elif k == "\x0e":  # ^N
            if not self._composing_new_thread:
                # start composing a new message
                self._composing_new_thread = True
                self.draw_keybindings()
                self.draw_edit_box()
                self.refresh_display()
            handled = True
        elif k == "\x1b":  # Esc
            if self._composing_new_thread:
                # start composing a new message
                self._composing_new_thread = False
                self.draw_keybindings()
                self.draw_edit_box()
                self.refresh_display()
            handled = True
        return handled

    def _base_handle_key(self, k):
        handled = False
        if k == "\x03":
            self.exit_requested = True
        elif k == "CTL_ENTER":  # normal enter is '\n'
            if self._edit_box.is_empty():
                pass
            else:
                self.send_message(self._edit_box.get_contents())
            self._edit_box.clear()
            self.draw_edit_box()
            self.draw_messages()
            self.refresh_display()
            self.refresh_display()
            handled = True
        elif k == "\x12":  # ^R
            self._fetch_new_messages()
            self.draw_messages()
            self.refresh_display()
            self.refresh_display()
            handled = True

        if not handled and self._in_compose_mode():
            # If we're in the channel root and we're not in compose mode,
            # ignore the character
            self._handle_text_input(k)

    def _in_compose_mode(self):
        return not (
            self._mode == ChatUI.CHANNEL_ROOT and not self._composing_new_thread
        )

    def _handle_text_input(self, k):
        if k == "KEY_A1":  # Home??
            self._edit_box.move_cursor_home()
            self.draw_edit_box()
            self.refresh_display()

        elif k == "KEY_C1":  # End??
            self._edit_box.move_cursor_end()
            self.draw_edit_box()
            self.refresh_display()

        elif k == "KEY_A2" or k == "KEY_UP":  # UP
            pass
        elif k == "KEY_C2" or k == "KEY_DOWN":  # DOWN
            pass

        elif k == "KEY_B1" or k == "KEY_LEFT":
            self._edit_box.move_cursor_left()
            self.draw_edit_box()
            self.refresh_display()

        elif k == "KEY_B3" or k == "KEY_RIGHT":
            self._edit_box.move_cursor_right()
            self.draw_edit_box()
            self.refresh_display()

        elif k == "PADSTOP":  # Delete? I suppose
            self._edit_box.delete_character()
            self.draw_edit_box()
            self.refresh_display()
            self.refresh_display()

        elif k == "\x08":
            self._edit_box.backspace_character()
            self.draw_edit_box()
            self.refresh_display()
            self.refresh_display()

        elif k == "\n":
            pass

        else:
            self._edit_box.insert_character(k)
            self.draw_edit_box()
            self.refresh_display()
            self.refresh_display()

    def start(self):
        curses.wrapper(ChatUI.main, self)

        # return self._selected_chat_message

    def refresh_display(self):
        caret_x, caret_y = self._edit_box.get_caret_xy()
        new_cursor_row = self.msg_box_origin_row + caret_y
        new_cursor_col = self.msg_box_origin_col + caret_x
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
        self.pad.clear()
        if self._mode == ChatUI.DIRECT_MESSAGE:
            self._draw_direct_messages()
        elif self._mode == ChatUI.GROUP_THREAD:
            self._draw_direct_messages()
        elif self._mode == ChatUI.CHANNEL_ROOT:
            self._draw_channels_threads()
        elif self._mode == ChatUI.CHANNEL_MESSAGE:
            self._draw_thread_message()

    def _draw_direct_messages(self):
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
                0,
                f"starting a new conversation with {self.other_user.display_name}",
            )
            curr_row += 1

    def _draw_channels_threads(self):
        self._toplevel_messages = []
        curr_row = 0
        curr_msg_index = 0
        for msg in self._channel.messages:
            if msg.is_toplevel():
                self._toplevel_messages.append(msg)

                if curr_msg_index == self._selected_thread_index:
                    self.pad.addstr(
                        curr_row,
                        0,
                        " ",
                        curses.color_pair(ChatUI.ACTIVE_THREAD_INDICATOR_COLOR),
                    )
                    self.pad.addstr(
                        curr_row + 1,
                        0,
                        " ",
                        curses.color_pair(ChatUI.ACTIVE_THREAD_INDICATOR_COLOR),
                    )

                username = f"{msg.sender.display_name}: "
                self.pad.addstr(
                    curr_row, 1, username, curses.color_pair(ChatUI.USERNAME_COLOR)
                )
                self.pad.addstr(curr_row, len(username) + 1, f"{msg.body}")
                curr_row += 1

                replies = msg.replies.all()
                num_replies = len(replies)
                active_attr = curses.color_pair(0) + (
                    curses.A_UNDERLINE
                    if curr_msg_index == self._selected_thread_index
                    else 0
                )
                if num_replies == 0:
                    self.pad.addstr(curr_row, 3, f"↳(no replies yet)", active_attr)
                elif num_replies == 1:
                    self.pad.addstr(curr_row, 3, f"↳1 reply", active_attr)
                else:
                    self.pad.addstr(curr_row, 3, f"↳{num_replies} replies", active_attr)
                curr_row += 1

                curr_msg_index += 1

                # print(f"@{msg.sender.display_name}: {msg.body}")
                # replies = msg.replies.all()
                # for reply in replies:
                #     print(f"\t@{reply.sender.display_name}: {reply.body}")
        pass

    def _draw_thread_message(self):
        pass
        curr_row = 0
        msg = self._root_message

        username = f"{msg.sender.display_name}: "
        self.pad.addstr(curr_row, 0, username, curses.color_pair(ChatUI.USERNAME_COLOR))
        self.pad.addstr(curr_row, len(username), f"{msg.body}")
        curr_row += 1

        replies = msg.replies.all()
        for reply in replies:
            username = f"  {reply.sender.display_name}: "
            self.pad.addstr(
                curr_row, 0, username, curses.color_pair(ChatUI.USERNAME_COLOR)
            )
            self.pad.addstr(curr_row, len(username), f"{reply.body}")
            curr_row += 1

    def send_message(self, message):
        if self._mode == ChatUI.DIRECT_MESSAGE:
            self._send_direct_message(message)
        elif self._mode == ChatUI.GROUP_THREAD:
            self._send_direct_message(message)
        elif self._mode == ChatUI.CHANNEL_ROOT:
            self._create_new_thread(message)
        elif self._mode == ChatUI.CHANNEL_MESSAGE:
            self._reply_to_thread(message)

    def _send_direct_message(self, message):
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

    def _create_new_thread(self, message):
        db = self.instance.get_db()
        graph = self.instance.get_graph_session()
        response = helpers.send_channel_message(
            graph,
            team_id=self._team.graph_id,
            channel_id=self._channel.graph_id,
            message=message,
        )
        resp_json = response.json()

        msg_model = get_or_create_message_model(db, resp_json)
        msg_model.from_id = self.current_user.id
        db.session.commit()

    def _reply_to_thread(self, message):
        db = self.instance.get_db()
        graph = self.instance.get_graph_session()
        response = helpers.send_channel_message_reply(
            graph,
            team_id=self._team.graph_id,
            channel_id=self._channel.graph_id,
            parent_msg_id=self._root_message.graph_id,
            message=message,
        )
        resp_json = response.json()

        msg_model = get_or_create_message_model(db, resp_json)
        msg_model.from_id = self.current_user.id
        db.session.commit()

    def _get_raw_title(self):
        if self._mode == ChatUI.DIRECT_MESSAGE:
            return f"chatting with {self.other_user.display_name}"
        elif self._mode == ChatUI.GROUP_THREAD:
            return f"chatting with group..."
        elif self._mode == ChatUI.CHANNEL_ROOT:
            return (
                f"all threads in {self._team.display_name}/{self._channel.display_name}"
            )
        elif self._mode == ChatUI.CHANNEL_MESSAGE:
            return f"chatting in {self._team.display_name}/{self._channel.display_name}"

    def _get_prompt(self):
        if self._mode == ChatUI.DIRECT_MESSAGE:
            return "Enter a message:"
        elif self._mode == ChatUI.GROUP_THREAD:
            return "Enter a message:"
        elif self._mode == ChatUI.CHANNEL_ROOT:
            return "Start a thread: "
        elif self._mode == ChatUI.CHANNEL_MESSAGE:
            return "Enter a message:"

    def _fetch_new_messages(self):
        if self._mode == ChatUI.DIRECT_MESSAGE:
            TeamsCacheCommand.cache_all_messages(self.instance, quiet=True)
        elif self._mode == ChatUI.GROUP_THREAD:
            TeamsCacheCommand.cache_all_messages(self.instance, quiet=True)
        elif self._mode == ChatUI.CHANNEL_ROOT:
            TeamsTeamCommand.cache_messages_in_channel(
                self.instance, self._channel, quiet=True
            )
        elif self._mode == ChatUI.CHANNEL_MESSAGE:
            TeamsTeamCommand.cache_replies_to_message(
                self.instance, self._root_message, quiet=True
            )
