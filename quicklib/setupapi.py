import os
import sys

import setuptools

from .utils import is_packaging
from .versioning import read_module_version
from .commands import CleanEggInfo, ExportMetadata
from .versioning import VersionSetByGit
from .incorporator import BundleIncorporatedZip
from .scripting import CreateScriptHooks
from .virtualfiles import UndoVirtualFiles, undo_virtual_files
from .datafiles import PrepareManifestIn
from .requirements import UseRequirementsTxtCommand, DynamicRequirementsCommand, FreezeRequirementsCommand


class SetupModifier(object):
    def __init__(self, auto_find_packages=True):
        self.auto_find_packages = auto_find_packages
        self.use_requirements_txt = True
        self.freeze_requirements = False
        self.version_module_paths = []
        self.module_level_scripts = {}

    def set_use_requirements_txt(self, flag_value):
        self.use_requirements_txt = flag_value

    def set_freeze_requirements(self, flag_value):
        self.freeze_requirements = flag_value

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
                self.cmd_opt_setdefault(kwargs, 'version_set_by_git', 'version_module_paths', self.version_module_paths)
            else:
                kwargs['version'] = read_module_version(self.version_module_paths[0])

        if self.module_level_scripts:
            self.cmd_opt_setdefault(kwargs, 'create_script_hooks', 'script_modules', self.module_level_scripts.values())
            kwargs \
                .setdefault('entry_points', {}) \
                .setdefault('console_scripts', []) \
                .extend([
                    "%(script_name)s=%(hook_module)s:%(func_name)s" % dict(
                        script_name=script_name,
                        hook_module=hook_module,
                        func_name=func_name,
                    )
                    for (script_name, (_, hook_module, func_name)) in zip(
                        self.module_level_scripts.keys(),
                        CreateScriptHooks.target_module_names_to_hook_module_and_func_name(self.module_level_scripts.values())
                    )
                ])

        if self.auto_find_packages and 'packages' not in kwargs:
            kwargs['packages'] = setuptools.find_packages()
            print "note: packages auto-discovered:"
            for p in kwargs['packages']:
                print "  - %s" % (p,)

        kwargs.setdefault('cmdclass', {}).update(self.get_quicklib_commands())

        orig_script_args = kwargs.pop('script_args', sys.argv[1:])
        script_args = []
        if is_packaging():
            script_args += [CleanEggInfo.SHORTNAME]
            if self.use_requirements_txt:
                script_args += [UseRequirementsTxtCommand.SHORTNAME]
            if self.freeze_requirements:
                script_args += [FreezeRequirementsCommand.SHORTNAME]
            script_args += [DynamicRequirementsCommand.SHORTNAME]
            script_args += [BundleIncorporatedZip.SHORTNAME]
            if self.version_module_paths:
                script_args += [VersionSetByGit.SHORTNAME]
            if self.module_level_scripts:
                script_args += [CreateScriptHooks.SHORTNAME, CreateScriptHooks.SHORTNAME]
            script_args += [PrepareManifestIn.SHORTNAME]
            script_args += orig_script_args
            script_args += [UndoVirtualFiles.SHORTNAME]
        else:
            script_args += [DynamicRequirementsCommand.SHORTNAME]
            script_args += orig_script_args
        kwargs['script_args'] = script_args

    @classmethod
    def get_quicklib_commands(cls):
        return {
            cmd_class.SHORTNAME: cmd_class
            for cmd_class in [
                CleanEggInfo, ExportMetadata, VersionSetByGit, BundleIncorporatedZip, CreateScriptHooks,
                UndoVirtualFiles, PrepareManifestIn, UseRequirementsTxtCommand, FreezeRequirementsCommand,
                DynamicRequirementsCommand,
            ]
        }

    @classmethod
    def cmd_opt_setdefault(cls, kwargs, cmd, opt, default):
        return kwargs.setdefault('command_options', {}).setdefault(cmd, {}).setdefault(opt, ('setup.py', default))[1]


# TODO: can this be replaced by a Distribution subclass? some of it?
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
    if 'use_requirements_txt' in kwargs:
        sm.set_use_requirements_txt(kwargs.pop('use_requirements_txt'))
    if 'freeze_requirements' in kwargs:
        sm.set_freeze_requirements(kwargs.pop('freeze_requirements'))
    if 'version_module_paths' in kwargs:
        sm.set_version_modules(kwargs.pop('version_module_paths'))
    if 'module_level_scripts' in kwargs:
        sm.set_module_level_scripts(kwargs.pop('module_level_scripts'))
    try:
        return sm.setup(**kwargs)
    except:
        try:
            print "quicklib.setup: emergency undoing of all virtual file changes"
            undo_virtual_files()
        except Exception as exc:
            print "ignoring exception thrown from error-case call to undo_virtual_files (%s)" % exc
        raise
