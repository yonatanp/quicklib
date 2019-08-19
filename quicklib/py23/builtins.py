"""This file mimicks the `builtins` package from `future` library.
However, it exists and should work nicely in both python2 and python3.
We use it to avoid having to conditionally load future's `builtin` package from our incorporated zip.
"""
from __future__ import absolute_import
import sys
__future_module__ = True

if sys.version_info[0] < 3:
    from __builtin__ import *
    # Overwrite any old definitions with the equivalent future.builtins ones:
    from future.builtins import *
else:
    from builtins import *
