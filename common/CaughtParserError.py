class CaughtParserError(Exception):
    """An error from creating or using an argument (optional or positional).

    The string value of this exception is the message, augmented with
    information about the argument that caused it.
    """

    def __init__(self, message):     
        self.message = message

    def __str__(self):
        return self.message