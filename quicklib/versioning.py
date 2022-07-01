import os
import re
import subprocess
import textwrap

from setuptools import Command
from distutils import log

from quicklib.virtualfiles import put_file
from .virtualfiles import modify_file

DEV_VERSION = "0.0.0.dev0"

RE_VERSION_CODE_LINE = re.compile("^__version__ *= *.*$", re.MULTILINE)


def create_version_block(version_value_repr="DEV_VERSION"):
    return textwrap.dedent("""
        # quicklib version boilerplate
        DEV_VERSION = "%(DEV_VERSION)s"
        __version__ = %(version_value_repr)s
        """ % dict(
            DEV_VERSION=DEV_VERSION,
            version_value_repr=version_value_repr,
        ))[1:-1]


def normalize_version_module_path(version_module_path):
    if os.path.isdir(version_module_path):
        version_module_path = os.path.join(version_module_path, "__version__.py")
    root, ext = os.path.splitext(version_module_path)
    if ext.lower() in (".pyo", ".pyc"):
        ext = ".py"
    if ext != ".py":
        raise ValueError("invalid version module path: %s" % version_module_path)
    return root + ext


def read_module_version(version_module_path):
    version_module_path = normalize_version_module_path(version_module_path)
    version_load_vars = {}
    exec(open(version_module_path).read(), version_load_vars)
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
        elif isinstance(self.version_module_paths, str):
            self.version_module_paths = list(map(str.strip, self.version_module_paths.split(",")))
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
            version_module_path = normalize_version_module_path(version_module_path)
            self._virtual_set_module_version(version_module_path, self.version)

    @classmethod
    def _virtual_set_module_version(cls, module_path, version):
        """
        create or modify (virtually) the module at the given path to have a `__version__ = [version]` code line.
        """
        if not isinstance(module_path, str):
            raise TypeError("expected string module path, got %r" % (module_path,))
        if not os.path.splitext(module_path)[1].lower() == ".py":
            raise ValueError("expected module path of a python source (.py) file, got %s" % (module_path,))
        if os.path.exists(module_path):
            version_module_code = open(module_path, "r").read()
            if not re.search(RE_VERSION_CODE_LINE, version_module_code):
                raise Exception("no version line (matching %s) found in %s, unable to replace module version" % (
                    RE_VERSION_CODE_LINE, module_path,
                ))
            # set any version line to the given specific string version (virtual - for package only)
            modified_code = re.sub(RE_VERSION_CODE_LINE, "__version__ = '%s'" % version, version_module_code)
            modify_file(module_path, modified_code, binary=False)
        else:
            put_file(module_path, create_version_block(repr(version)))


class GitVersionCalculator:
    """determine library version based on git tags and git-describe"""
    def getVersion(self):
        git_describe = subprocess.check_output('git describe --match "[[:digit:]]*.[[:digit:]]*" --dirty=_dirty',
                                               shell=True, encoding='ascii')
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


# exposed as a standalone utility
def calculate_git_version():
    print(GitVersionCalculator().getVersion())
