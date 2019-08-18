"""Utilities for supporting py2/3 concurrently.
"""
import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

# for subprocess
encoding_ascii = {'encoding': 'ascii'} if PY3 else {}
