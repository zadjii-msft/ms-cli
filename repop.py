from common.ResultAndData import *
from common.Instance import Instance
from models.User import User
from models.ChatMessage import ChatMessage


def main():
    instance = Instance()
    db = instance.get_db()

    # This file can be used for some quick populating of the DB with dummy data.
    # Now that `ms teams cache` is working, it's less important now.


if __name__ == "__main__":
    main()
