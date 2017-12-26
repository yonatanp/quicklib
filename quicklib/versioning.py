import re
import subprocess
import types

from setuptools import Command


DEV_VERSION = "0.0.0.dev0"
RE_VERSION_CODE_LINE = re.compile("^__version__ = .*$", re.MULTILINE)


def replace_module_version(module_file_path, new_version):
    """Edits the source file and changes the code line above to point to the given `new_version`"""
    # chomp off '.pyc' or '.pyo' if given into a clean '.py' extension
    if module_file_path.lower().endswith(".pyc") or module_file_path.lower().endswith(".pyo"):
        module_file_path = module_file_path[:-1]
    module_code = open(module_file_path, "rb").read()
    if new_version != DEV_VERSION:
        # setting a specific string version
        module_code = re.sub(RE_VERSION_CODE_LINE, "__version__ = '%s'" % new_version, module_code)
    else:
        # reverting to DEV_VERSION, just use the constant in the code line
        module_code = re.sub(RE_VERSION_CODE_LINE, "__version__ = DEV_VERSION", module_code)
    open(module_file_path, "wb").write(module_code)


def read_module_version(version_module_path):
    version_load_vars = {}
    execfile(version_module_path, version_load_vars)
    return version_load_vars['__version__']


class VersionSetCommandBase(Command):
    user_options = [
        ("writeversionfile=", None,
         "path of file to be overwritten with the git-based version calculated for this build"),
    ]

    # Note: override this with all the 'version' submodules of packages you wish to version
    # See this package's 'version.py' for an example module to be copy-pasted
    # TODO: get rid of copy-pasting and auto-add version.py if possible
    PACKAGE_VERSION_MODULES = []

    # The way we calculate versions - implement in subclasses
    VERSION_CALCULATOR = None

    @classmethod
    def with_version_modules(cls, modules):
        class cls_with_version_modules(cls):
            PACKAGE_VERSION_MODULES = list(modules)
        return cls_with_version_modules

    def initialize_options(self):
        self.writeversionfile = None

    def finalize_options(self):
        pass

    def run(self):
        # we generate the version of the package, update it in all needed places, and write back to user if asked nicely
        self.version = self.VERSION_CALCULATOR.getVersion()
        self._updateVersion()
        self._writeVersionIfNeeded()

    def _updateVersion(self):
        # change the value set in the distribution object for the following setuptools commands
        self.distribution.metadata.version = self.version
        # set versions for all modules needed
        for version_module in self.PACKAGE_VERSION_MODULES:
            # TODO: choose one pattern and stick to it
            if isinstance(version_module, types.ModuleType):
                # change the version in the already-loaded module (for this current python session)
                version_module.__version__ = self.version
                # actually change the code to get packaged along with the hard-coded version
                version_module.replace_this_module_version(self.version)
            elif isinstance(version_module, basestring):
                replace_module_version(version_module, self.version)
            else:
                raise Exception("cannot update version for %r" % (version_module,))

    def _writeVersionIfNeeded(self):
        if self.writeversionfile:
            open(self.writeversionfile, "w").write(self.version)


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


# Used to "revert to dev version"
class DevVersionCalculator(object):
    def getVersion(self):
        return DEV_VERSION


class VersionSetByGit(VersionSetCommandBase):
    SHORTNAME="version_set_by_git"
    description = "set package version from git info"
    VERSION_CALCULATOR = GitVersionCalculator()


class VersionResetToDev(VersionSetCommandBase):
    SHORTNAME="version_reset_to_dev"
    description = "reset package version to DEV_VERSION"
    VERSION_CALCULATOR = DevVersionCalculator()
