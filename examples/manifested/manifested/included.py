import os


def show_text():
    print(open(os.path.join(os.path.dirname(__file__), "some_text.txt"), "r").read())


def verify_exclusion():
    try:
        from . import excluded
    except ImportError:
        print("success")
    else:
        print("failed!")
        raise Exception("managed to import excluded, but manifest should exclude it")
