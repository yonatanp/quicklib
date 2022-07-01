"""Helper module for managing files that we want to create or modify before we package our library.
"""
import contextlib
import os

from setuptools import Command
from distutils import log


class _VirtualFileRegistry:
    def __init__(self):
        self.removal = []
        self.reversal = {}

    def register_file_for_removal(self, path):
        if path in self.removal:
            raise Exception("cannot register path %s for removal: already registered for removal")
        if path in self.reversal:
            raise Exception("cannot register path %s for removal: already registered for reversal")
        if not os.path.exists(path):
            raise Exception("cannot register path %s for removal: file does not exist")
        if not os.path.isfile(path):
            raise Exception("cannot register path %s for removal: not a regular file")
        self.removal.append(path)

    def register_file_for_reversal(self, path):
        if path in self.removal:
            raise Exception("cannot register path %s for reversal: already registered for removal")
        if path in self.reversal:
            raise Exception("cannot register path %s for reversal: already registered for reversal")
        if not os.path.exists(path):
            raise Exception("cannot register path %s for reversal: file does not exist")
        if not os.path.isfile(path):
            raise Exception("cannot register path %s for reversal: not a regular file")
        self.reversal[path] = open(path, "rb").read()

    def remove(self, pre_callback=None):
        try:
            for p in self.removal:
                if pre_callback is not None:
                    pre_callback(p)
                try:
                    os.unlink(p)
                except Exception as exc:
                    print("error: failed to remove build-time created file %s, left on disk (exc: %s)" % (p, exc))
        finally:
            self.removal = []

    def revert(self, pre_callback=None):
        try:
            for p, original_content in self.reversal.items():
                if pre_callback is not None:
                    pre_callback(p)
                try:
                    open(p, "wb").write(original_content)
                except Exception as exc:
                    print("error: failed to revert build-time modified file %s, left on disk in modified form (exc: %s)" % (p, exc))
        finally:
            self.reversal = {}


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


def register_for_removal(path):
    virtual_file_registry.register_file_for_removal(path)


def modify_file(path, content, binary=False):
    if not os.path.exists(path):
        raise Exception("cannot virtually modify file at %s, file already exists" % path)
    virtual_file_registry.register_file_for_reversal(path)
    mode = "wb" if binary else "w"
    open(path, mode).write(content)


def register_for_reversal(path):
    virtual_file_registry.register_file_for_reversal(path)


class UndoVirtualFiles(Command):
    SHORTNAME = "undo_virtual_files"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        virtual_file_registry.remove(pre_callback=lambda fn: log.info("cleaning up virtual file %s..." % fn))
        virtual_file_registry.revert(pre_callback=lambda fn: log.info("undoing virtual changes to file %s..." % fn))


def undo_virtual_files():
    virtual_file_registry.remove()
    virtual_file_registry.revert()
