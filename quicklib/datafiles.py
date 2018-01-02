import datetime
import os
import textwrap

from setuptools import Command

from .virtualfiles import modify_file, put_file


class ManifestInRewriter(object):
    def __init__(self, path="MANIFEST.in", append=True):
        self.path = path
        self.append = append
        self.lines = []
        self.rewritten = False

    def add_line(self, line_text):
        if self.rewritten:
            raise Exception("cannot add lines: %s has already been rewritten" % (self.path,))
        self.lines.append(line_text)

    def add_comment(self, comment_line):
        self.add_line("# %s" % comment_line)

    def add_include(self, *patterns):
        if not patterns:
            raise ValueError("at least one pattern is required for include")
        self.add_line("include %s" % " ".join(patterns))

    def add_exclude(self, *patterns):
        if not patterns:
            raise ValueError("at least one pattern is required for exclude")
        self.add_line("exclude %s" % " ".join(patterns))

    def add_recursive_include(self, directory, *patterns):
        if not patterns:
            raise ValueError("at least one pattern is required for recursive-include")
        self.add_line("recursive-include %s %s" % (directory, " ".join(patterns)))

    def add_recursive_exclude(self, directory, *patterns):
        if not patterns:
            raise ValueError("at least one pattern is required for recursive-exclude")
        self.add_line("recursive-exclude %s %s" % (directory, " ".join(patterns)))

    def add_global_include(self, *patterns):
        if not patterns:
            raise ValueError("at least one pattern is required for global-include")
        self.add_line("global-include %s" % " ".join(patterns))

    def add_global_exclude(self, *patterns):
        if not patterns:
            raise ValueError("at least one pattern is required for global-exclude")
        self.add_line("global-exclude %s" % " ".join(patterns))

    def add_prune(self, directory):
        self.add_line("prune %s" % directory)

    def add_graft(self, directory):
        self.add_line("graft %s" % directory)

    def rewrite(self):
        if self.rewritten:
            raise Exception("cannot rewrite: %s has already been rewritten" % (self.path,))
        if not self.lines:
            self.rewritten = True
            return
        text = textwrap.dedent("""
            # ---- AUTO-GENERATED: lines beyond this point were added by %(me)s at %(when)s
            %(joined_lines)s
            # ---- AUTO-GENERATED: done
        """[1:-1]) % dict(
            me=__name__, when=datetime.datetime.now().strftime("%c"), joined_lines="\n".join(self.lines),
        )
        if self.append and os.path.exists(self.path):
            text = open(self.path, "r").read() + "\n" + text
        if os.path.exists(self.path):
            modify_file(self.path, text)
        else:
            put_file(self.path, text)
        self.rewritten = True


class PrepareManifestIn(Command):
    SHORTNAME = "prepare_manifest_in"

    user_options = [
        ("extra-lines=", None,
         "extra lines to add to the MANIFEST.in file (list or comma-separated string)")
    ]

    def initialize_options(self):
        self.extra_lines = []

    def finalize_options(self):
        if isinstance(self.extra_lines, basestring):
            self.extra_lines = self.extra_lines.split(",")

    def run(self):
        rewriter = ManifestInRewriter()
        for line in self.extra_lines:
            rewriter.add_line(line)
        rewriter.rewrite()
