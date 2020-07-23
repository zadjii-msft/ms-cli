from common.ResultAndData import *
from common.Instance import Instance
from models.User import User
from models.ChatMessage import ChatMessage


def main():
    instance = Instance()
    db = instance.get_db()

    # user0 = User("zadjii")
    # user1 = User("miniksa")
    # user2 = User("lolboy")
    # db.session.add(user0)
    # db.session.add(user1)
    # db.session.add(user2)
    # db.session.commit()

    # msg_0_0 = ChatMessage(user0, user1, "message 0 from user0")
    # msg_1_0 = ChatMessage(user1, user0, "message 0 from user1")
    # msg_0_1 = ChatMessage(user0, user1, "message 1 from user0")
    # msg_1_1 = ChatMessage(user1, user0, "message 1 from user1")
    # msg_0_2 = ChatMessage(user0, user1, "message 2 from user0")
    # msg_1_2 = ChatMessage(user1, user0, "message 2 from user1")

    # msg_a = ChatMessage(user0, user2, "message to lolboy from user0")
    # msg_b = ChatMessage(user0, user2, "and another")
    # msg_c = ChatMessage(user0, user2, "lolboy isnt very talkative")
    # msg_d = ChatMessage(user2, user0, "watch your mouth son")
    # msg_e = ChatMessage(user0, user2, "whatever")

    # db.session.add(msg_0_0)
    # db.session.add(msg_1_0)
    # db.session.add(msg_0_1)
    # db.session.add(msg_1_1)
    # db.session.add(msg_0_2)
    # db.session.add(msg_1_2)

    # db.session.add(msg_a)
    # db.session.add(msg_b)
    # db.session.add(msg_c)
    # db.session.add(msg_d)
    # db.session.add(msg_e)

    # db.session.commit()


if __name__ == "__main__":
    main()
