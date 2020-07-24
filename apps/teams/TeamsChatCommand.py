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

    def __init__(self, instance, thread, other_user):
        self.instance = instance
        self.thread = thread
        self.other_user = other_user
        self.current_user = instance.get_current_user().data

        self.stdscr = None
        self.editwin = None
        self.pad = None
        self.input_line = ''

    @staticmethod
    def main(stdscr, self):
        self.stdscr = stdscr

        curses.use_default_colors()
        # Clear screen
        stdscr.clear()


        curses.init_pair(ChatUI.TITLE_COLOR, curses.COLOR_WHITE, curses.COLOR_MAGENTA)
        curses.init_pair(ChatUI.USERNAME_COLOR, curses.COLOR_BLACK, -1)
        curses.init_pair(ChatUI.DATETIME_COLOR, curses.COLOR_BLACK, -1)
        curses.init_pair(ChatUI.FOCUSED_INPUT_COLOR, -1, -1)
        curses.init_pair(ChatUI.UNFOCUSED_INPUT_COLOR, curses.COLOR_BLACK, curses.COLOR_WHITE)

        # Your application can determine the size of the screen by using the
        # curses.LINES and curses.COLS variables to obtain the y and x
        # sizes. Legal coordinates will then extend from (0,0) to
        # (curses.LINES - 1, curses.COLS - 1).
        window_width = curses.COLS - 1
        window_height = curses.LINES - 1

        title = f'chatting with {self.other_user.display_name}' if self.other_user else 'group...'
        title += (' ' * (window_width - len(title)))
        prompt = 'Enter a message:'
        # stdscr.addstr(0, 0, title, curses.A_REVERSE)
        stdscr.addstr(0, 0, title, curses.color_pair(ChatUI.TITLE_COLOR))

        # # This raises ZeroDivisionError when i == 10.
        # for i in range(0, 9):
        #     v = i-10
        #     sleep(.5)
        #     stdscr.addstr(i, 0, '10 divided by {} is {}'.format(v, 10/v))
        #     stdscr.refresh()

        # stdscr.getkey()


        message_box_height = 2
        message_box_width = window_width - len(prompt) - 2
        msg_box_origin_row = window_height-message_box_height
        msg_box_origin_col = len(prompt) + 1
        # editwin = curses.newwin(msg_box_origin_row, msg_box_origin_col, message_box_height, message_box_width)
        # editwin = curses.newwin(height, width, y, x)
        editwin = curses.newwin(message_box_height, message_box_width, msg_box_origin_row, msg_box_origin_col)
        # editwin.border('a', 'b')
        editwin.bkgd(' ', curses.color_pair(ChatUI.UNFOCUSED_INPUT_COLOR))

        stdscr.addstr(msg_box_origin_row, 0, prompt)
        stdscr.refresh()

        self.pad = curses.newpad(100, window_width)
        chat_history_height = window_height - (message_box_height + 1)

        self.draw_messages()
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
        # pad.refresh( 0,0, 1,0, chat_history_height+1,window_width)

        # stdscr.refresh()


        def refresh_display(self):
            new_cursor_row = msg_box_origin_row + 0
            new_cursor_col = msg_box_origin_col + len(self.input_line)
            # msg_box_origin_col
            # editwin.move(0, len(input_line))
            stdscr.move(new_cursor_row, new_cursor_col)

            stdscr.refresh()
            editwin.refresh()
            self.pad.refresh( 0,0, 1,0, chat_history_height,window_width)
        refresh_display(self)

        exit_requested = False
        while not exit_requested:
            k = stdscr.getkey()
            if k == '\x03':
                exit_requested = True
            elif k == '\n':
                # editwin.border('a', 'b')

                if self.input_line == None or self.input_line == '':
                    pass
                else:
                    self.send_message(self.input_line)
                    # pad.addstr(curr_row, 0, self.input_line)
                    # curr_row+=1
                # stdscr.refresh()
                # pad.refresh( 0,0, 1,0, chat_history_height+1,window_width)
                self.input_line = ''
                # editwin.addstr(0, 0, input_line)
                editwin.clear()
                self.draw_messages()
                # editwin.refresh()
                refresh_display(self)
                refresh_display(self)

            if k == '\x08':
                self.input_line = self.input_line[:-1]
                editwin.clear()
                editwin.addstr(0, 0, self.input_line)
                refresh_display(self)
                refresh_display(self)
            else:
                self.input_line += k

                editwin.addstr(0, 0, self.input_line)
                # stdscr.refresh()
                # editwin.refresh()
                # pad.refresh( 0,0, 1,0, chat_history_height+1,window_width)
                refresh_display(self)
                refresh_display(self)

    def start(self):
        curses.wrapper(ChatUI.main, self)

    def draw_messages(self):
        messages = self.thread.messages.order_by(ChatMessage.created_date_time).all()
        curr_row = 0
        for msg in messages:
            username = f'{msg.sender.display_name}: '
            self.pad.addstr(curr_row, 0, username, curses.color_pair(ChatUI.USERNAME_COLOR))
            self.pad.addstr(curr_row, len(username), f'{msg.body}')
            curr_row+=1
        if len(messages) == 0:
            self.pad.addstr(curr_row, len(username), f'starting a new conversation with {msg.sender.display_name}')
            curr_row+=1

    def send_message(self, message):
        db = self.instance.get_db()
        graph = self.instance.get_graph_session()
        response = helpers.send_chat_message(graph, chat_id=self.thread.graph_id, message=message)
        resp_json = response.json()

        msg_model = get_or_create_message_model(db, resp_json)
        msg_model.thread_id = self.thread.id
        # from_id = response["from"]["user"]["id"]
        # Make sure user {from_id} is in the db
        # user_json = helpers.get_user(graph, user_id=from_id)
        # sender = get_or_create_user_model(db, user_json)
        msg_model.from_id = self.current_user.id
        db.session.commit()

        # response = helpers.send_message(session, team_id=team_id, channel_id=chat_id, message="farts")
        # response = helpers.send_chat_message(
        #     session,
        #     chat_id=chat_id,
        #     message="hey michael this is a message mike using the tool",
        # )
        # print(response)



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

        chat_ui = ChatUI(instance, target_thread, matched_user)
        chat_ui.start()

        return Success()


# {
#     "@odata.context": "https://graph.microsoft.com/beta/$metadata#users('fea82a37-a67e-487c-bce2-1e6bff957567')/chats('19%3A4c5e2a9f-3f3b-4b94-97fc-b0d20bf1cdb6_fea82a37-a67e-487c-bce2-1e6bff957567%40unq.gbl.spaces')/messages/$entity",
#     "id": "1595613002430",
#     "replyToId": null,
#     "etag": "1595613002430",
#     "messageType": "message",
#     "createdDateTime": "2020-07-24T17:50:02.43Z",
#     "lastModifiedDateTime": null,
#     "deletedDateTime": null,
#     "subject": null,
#     "summary": null,
#     "chatId": "19:4c5e2a9f-3f3b-4b94-97fc-b0d20bf1cdb6_fea82a37-a67e-487c-bce2-1e6bff957567@unq.gbl.spaces",
#     "importance": "normal",
#     "locale": "en-us",
#     "webUrl": null,
#     "channelIdentity": null,
#     "policyViolation": null,
#     "from": {
#         "application": null,
#         "device": null,
#         "conversation": null,
#         "user": {
#             "id": "fea82a37-a67e-487c-bce2-1e6bff957567",
#             "displayName": "zadjii",
#             "userIdentityType": "aadUser"
#         }
#     },
#     "body": {
#         "contentType": "text",
#         "content": "This is from the graph explorer, does it actually do the POST?"
#     },
#     "attachments": [],
#     "mentions": [],
#     "reactions": []
# }
