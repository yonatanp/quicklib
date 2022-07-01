import datetime
import os
import textwrap

from setuptools import Command
from distutils import log

from .virtualfiles import modify_file, put_file


class ManifestInRewriter:
    def __init__(self, path=None, append=True):
        self.path = path
        self.append = append
        self.lines = []
        self.rewritten = False

    def set_path(self, path):
        # this allows us to delay moment of path selection to just before rewrite
        if self.rewritten:
            raise Exception("cannot set path: %s has already been rewritten" % (self.path,))
        self.path = path

    def set_append(self, append):
        # this allows us to delay moment of decision on append/replace to just before rewrite
        if self.rewritten:
            raise Exception("cannot set append: %s has already been rewritten" % (self.path,))
        self.append = append

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

    def prepend_lines(self, lines):
        self.lines = list(lines) + self.lines

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
        ("manifest-content", None,
         "use these lines as MANIFEST.in (virtually created/replaced); extra-lines, if given, are added"),
        ("extra-lines=", None,
         "extra lines to add to the MANIFEST.in file (list or comma-separated string)")
    ]

    def initialize_options(self):
        self.rewriter = ManifestInRewriter()
        self.manifest_content = None
        self.extra_lines = []

    def finalize_options(self):
        if isinstance(self.manifest_content, str):
            self.manifest_content = self.manifest_content.split("\n")
        if isinstance(self.extra_lines, str):
            self.extra_lines = self.extra_lines.split("\n")

    def run(self):
        template = self.get_finalized_command('sdist').template or "MANIFEST.in"
        self.rewriter.set_path(template)
        if self.manifest_content is not None:
            self.rewriter.set_append(False)
            self.rewriter.prepend_lines(list(self.manifest_content) + [''] * 2)
        for line in self.extra_lines:
            self.rewriter.add_line(line)
        log.info("rewriting %s" % self.rewriter.path)
        self.rewriter.rewrite()
