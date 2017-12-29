"""Helper module for managing files that we want to add to our library during packaging time.
"""
import contextlib
import os

from setuptools import Command
from distutils import log


class _VirtualFileRegistry(object):
    def __init__(self):
        self.removal = []

    def register_file_for_removal(self, path):
        if path in self.removal:
            raise Exception("cannot register path %s for removal: already registered for removal")
        if not os.path.exists(path):
            raise Exception("cannot register path %s for removal: file does not exist")
        if not os.path.isfile(path):
            raise Exception("cannot register path %s for removal: not a regular file")
        self.removal.append(path)

    def remove(self, pre_callback=None):
        try:
            for p in self.removal:
                if pre_callback is not None:
                    pre_callback(p)
                try:
                    os.unlink(p)
                except Exception as exc:
                    print "error: failed to remove build-time created file %s, left on disk (exc: %s)" % (p, exc)
        finally:
            self.removal = []


virtual_file_registry = _VirtualFileRegistry()


def put_file(path, content, binary=False):
    with open_file(path, binary=binary) as f:
        f.write(content)


@contextlib.contextmanager
def open_file(path, binary=False):
    if os.path.exists(path):
        raise Exception("cannot create virtual file at %s, file already exists" % path)
    mode = "wb" if binary else "w"
    f = open(path, mode)
    try:
        yield f
    finally:
        f.close()
        virtual_file_registry.register_file_for_removal(path)


class RemoveVirtualFiles(Command):
    SHORTNAME = "remove_virtual_files"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        virtual_file_registry.remove(pre_callback=lambda fn: log.info("cleaning up virtual file %s..." % fn))


def remove_virtual_files():
    virtual_file_registry.remove()
