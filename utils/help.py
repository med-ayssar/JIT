import inspect


def whichFunc():
    return inspect.stack()[1][3]
