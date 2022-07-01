import os


def is_packaging():
    return not os.path.exists("PKG-INFO")
