import os
import re
import subprocess
import textwrap

from setuptools import Command
from distutils import log

from .virtualfiles import modify_file

DEV_VERSION = "0.0.0.dev0"

RE_VERSION_CODE_LINE = re.compile("^__version__ *= *.*$", re.MULTILINE)


def create_version_block():
    return textwrap.dedent("""
        # quicklib version boilerplate
        DEV_VERSION = "%(DEV_VERSION)s"
        __version__ = DEV_VERSION
        """ % dict(DEV_VERSION=DEV_VERSION))[1:-1]


def read_module_version(version_module_path):
    version_load_vars = {}
    execfile(version_module_path, version_load_vars)
    return version_load_vars['__version__']


class VersionSetCommandBase(Command):
    user_options = [
        ("version-module-paths=", None,
         "list (or comma-separated) paths to modules where a __version__ line should be set")
    ]

    # The way we calculate versions - implement in subclasses
    VERSION_CALCULATOR = None

    def initialize_options(self):
        self.version_module_paths = None

    def finalize_options(self):
        if self.version_module_paths is None:
            self.version_module_paths = []
        elif isinstance(self.version_module_paths, basestring):
            self.version_module_paths = self.version_module_paths.split(",")
        if not self.version_module_paths:
            log.warn("warning: no version_module_paths provided, SetVersion command will have no effect")

    def run(self):
        # we generate the version of the package, update it in all needed places, and write back to user if asked nicely
        self.version = self.VERSION_CALCULATOR.getVersion()
        self._updateVersion()

    def _updateVersion(self):
        # change the value set in the distribution object for the following setuptools commands
        self.distribution.metadata.version = self.version
        # set versions for all modules needed
        for version_module_path in self.version_module_paths:
            self._virtual_replace_module_version(version_module_path, self.version)

    @classmethod
    def _virtual_replace_module_version(cls, module_path, new_version):
        """
        Edits the source file on disk and changes any `__version__ = ...` code line to use `new_version`.
        """
        if not isinstance(module_path, basestring):
            raise TypeError("expected string module path, got %r" % (module_path,))
        if not os.path.splitext(module_path)[1].lower() == ".py":
            raise ValueError("expected module path of a python source (.py) file, got %s" % (module_path,))
        version_module_code = open(module_path, "rb").read()
        if not re.search(RE_VERSION_CODE_LINE, version_module_code):
            raise Exception("no version line (matching %s) found in %s, unable to replace module version" % (
                RE_VERSION_CODE_LINE, module_path,
            ))
        # set any version line to the given specific string version (virtual - for package only)
        modified_code = re.sub(RE_VERSION_CODE_LINE, "__version__ = '%s'" % new_version, version_module_code)
        modify_file(module_path, modified_code, binary=True)


class GitVersionCalculator(object):
    """determine library version based on git tags and git-describe"""
    def getVersion(self):
        git_describe = subprocess.check_output('git describe --match "*.*" --dirty=_dirty', shell=True)
        return self.describe_to_version(git_describe)

    @classmethod
    def describe_to_version(cls, git_describe):
        if "-g" in git_describe:
            # we are a few commits past the latest version tag
            m = re.match("^(\\d+)\\.(\\d+)-(\\d+)-g([0-9a-f]+)(_dirty)?$", git_describe)
            if not m:
                raise Exception("Failed to parse the 'git describe' output: %r" % (git_describe,))
            (tag_major, tag_minor, num_commits_since_tag, _current_commit, dirty_mark) = m.groups()
            version = "%s.%s.%s" % (tag_major, tag_minor, num_commits_since_tag)
        else:
            # the latest commit has a version tag on it
            m = re.match("^(\\d+)\\.(\\d+)(_dirty)?$", git_describe)
            if not m:
                raise Exception("Failed to parse the 'git describe' output: %r" % (git_describe,))
            (tag_major, tag_minor, dirty_mark) = m.groups()
            version = "%s.%s" % (tag_major, tag_minor)
        if dirty_mark is not None:
            version += ".dirty"
        return version


class VersionSetByGit(VersionSetCommandBase):
    SHORTNAME = "version_set_by_git"
    description = "set library version from git info"
    VERSION_CALCULATOR = GitVersionCalculator()
