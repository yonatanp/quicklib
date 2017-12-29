import os
import sys

import setuptools

from .versioning import read_module_version


def is_packaging():
    return not os.path.exists("PKG-INFO")


class SetupModifier(object):
    def __init__(self, auto_find_packages=True):
        self.auto_find_packages = auto_find_packages
        self.version_module_paths = []

    def set_version_modules(self, module_paths):
        if not all(os.path.isfile(p) for p in module_paths):
            raise ValueError("invalid module_paths: all must be existing script files (module_paths=%s)" % (module_paths,))
        self.version_module_paths = list(module_paths)

    def setup(self, **kwargs):
        self._modify_setup_kwargs(kwargs)
        return setuptools.setup(**kwargs)

    def _modify_setup_kwargs(self, kwargs):
        if kwargs.pop('version', None) is not None and self.version_module_paths:
            raise ValueError("when specifying version modules, you must not also specify hard-coded `version` in setup")
        if kwargs.pop('version', None) is None and not self.version_module_paths:
            raise ValueError("you must either specify version modules or give a hard-coded `version` in setup")
        if self.version_module_paths:
            if is_packaging():
                kwargs['version'] = "ignored; replaced later by SetVersion command"
                kwargs \
                    .setdefault('command_options', {}) \
                    .setdefault('version_set_by_git', {}) \
                    .setdefault('version_module_paths', ('setup.py', self.version_module_paths))
            else:
                kwargs['version'] = read_module_version(self.version_module_paths[0])

        kwargs.setdefault('cmdclass', {}).update(self.get_quicklib_commands())

        if self.auto_find_packages and 'packages' not in kwargs:
            kwargs['packages'] = setuptools.find_packages()
            print "note: packages auto-discovered:"
            for p in kwargs['packages']:
                print "  - %s" % (p,)

        # # TODO: requirements are on the agenda
        # if 'install_requires' not in kwargs:
        #     pass

        if is_packaging():
            orig_script_args = kwargs.pop('script_args', sys.argv[1:])
            script_args = []
            script_args += ["clean_egg_info"]
            script_args += ["bundle_incorporated_zip"]
            if self.version_module_paths:
                script_args += ["version_set_by_git"]
            script_args += orig_script_args
            if self.version_module_paths:
                script_args += ["version_reset_to_dev"]
            script_args += ["clean_any_bundled_incorporated_zip"]
            kwargs['script_args'] = script_args

    @classmethod
    def get_quicklib_commands(cls):
        from .commands import CleanEggInfo, ExportMetadata
        from .versioning import VersionSetByGit, VersionResetToDev
        from .incorporator import BundleIncorporatedZip, CleanAnyBundledIncorporatedZip
        return {
            CleanEggInfo.SHORTNAME: CleanEggInfo,
            ExportMetadata.SHORTNAME: ExportMetadata,
            VersionSetByGit.SHORTNAME: VersionSetByGit,
            VersionResetToDev.SHORTNAME: VersionResetToDev,
            BundleIncorporatedZip.SHORTNAME: BundleIncorporatedZip,
            CleanAnyBundledIncorporatedZip.SHORTNAME: CleanAnyBundledIncorporatedZip,
        }


def setup(**kwargs):
    """
    setup a-la quicklib
    :param version_module_paths: list of module paths where a `__version__ = DEV_VERSION` statement is to be
        auto-replaced with git-based version string.
    :param kwargs: any of setuptools.setup kwargs, with some modified behavior:
        packages - if not given, find_packages() is applied automatically
    :return:
    """
    sm = SetupModifier()
    if 'version_module_paths' in kwargs:
        sm.set_version_modules(kwargs.pop('version_module_paths'))
    return sm.setup(**kwargs)
