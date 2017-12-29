import os
import sys

import setuptools

from .versioning import read_module_version
from .commands import CleanEggInfo, ExportMetadata
from .versioning import VersionSetByGit, VersionResetToDev
from .incorporator import BundleIncorporatedZip, CleanAnyBundledIncorporatedZip
from .scripting import CreateScriptHooks
from .virtualfiles import RemoveVirtualFiles


def is_packaging():
    return not os.path.exists("PKG-INFO")


class SetupModifier(object):
    def __init__(self, auto_find_packages=True):
        self.auto_find_packages = auto_find_packages
        self.version_module_paths = []
        self.module_level_scripts = {}

    def set_version_modules(self, module_paths):
        if not all(os.path.isfile(p) for p in module_paths):
            raise ValueError("invalid module_paths: all must be existing script files (module_paths=%s)" % (module_paths,))
        self.version_module_paths = list(module_paths)

    def set_module_level_scripts(self, script_names_to_module_names):
        self.module_level_scripts = script_names_to_module_names

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

        if self.module_level_scripts:
            kwargs \
                .setdefault('command_options', {}) \
                .setdefault('create_script_hooks', {}) \
                .setdefault('script_modules', ('setup.py', self.module_level_scripts.values()))
            kwargs \
                .setdefault('entry_points', {}) \
                .setdefault('console_scripts', []) \
                .extend([
                    "%(script_name)s=%(script_hook_name)s:main" % dict(
                        script_name=script_name,
                        script_hook_name=CreateScriptHooks.module_to_script_hook_module(module_name),
                    )
                    for (script_name, module_name) in self.module_level_scripts.iteritems()
                ])

        if self.auto_find_packages and 'packages' not in kwargs:
            kwargs['packages'] = setuptools.find_packages()
            print "note: packages auto-discovered:"
            for p in kwargs['packages']:
                print "  - %s" % (p,)

        # # TODO: requirements are on the agenda
        # if 'install_requires' not in kwargs:
        #     pass

        kwargs.setdefault('cmdclass', {}).update(self.get_quicklib_commands())

        if is_packaging():
            orig_script_args = kwargs.pop('script_args', sys.argv[1:])
            script_args = []
            script_args += [CleanEggInfo.SHORTNAME]
            script_args += [BundleIncorporatedZip.SHORTNAME]
            if self.version_module_paths:
                script_args += [VersionSetByGit.SHORTNAME]
            if self.module_level_scripts:
                script_args += [CreateScriptHooks.SHORTNAME]
            script_args += orig_script_args
            if self.version_module_paths:
                script_args += [VersionResetToDev.SHORTNAME]
            script_args += [CleanAnyBundledIncorporatedZip.SHORTNAME]
            if self.module_level_scripts:
                script_args += [RemoveVirtualFiles.SHORTNAME]
            kwargs['script_args'] = script_args

    @classmethod
    def get_quicklib_commands(cls):
        return {
            cmd_class.SHORTNAME: cmd_class
            for cmd_class in [
                CleanEggInfo, ExportMetadata, VersionSetByGit, VersionResetToDev, BundleIncorporatedZip,
                CleanAnyBundledIncorporatedZip, CreateScriptHooks, RemoveVirtualFiles,
            ]
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
    if 'module_level_scripts' in kwargs:
        sm.set_module_level_scripts(kwargs.pop('module_level_scripts'))
    return sm.setup(**kwargs)
