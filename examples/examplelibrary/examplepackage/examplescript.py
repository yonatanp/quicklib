"""This is a module that can also be run as a script.
It is registered by setup.py so that once the library is installed, the script can independently be executed.
"""
import sys


def do_something(args):
    print("doing something on %s" % (args,))


if __name__ == '__main__':
    print("examplepackage.examplescript __main__ running...")
    do_something(sys.argv[1:])
