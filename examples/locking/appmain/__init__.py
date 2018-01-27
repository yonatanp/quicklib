import pkg_resources

import pytz

from .__version__ import __version__


def main():
    print "pytz version:", pkg_resources.get_distribution("pytz")
    print "app version:", pkg_resources.get_distribution("app-lib")
    print "app __version__:", __version__
