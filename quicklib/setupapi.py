import os
import sys

import setuptools
from setuptools.command.sdist import sdist as setuptools_sdist
from setuptools.command.egg_info import manifest_maker, egg_info as setuptools_egg_info

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
        self.freeze_requirements_params = {}
        self.version_module_paths = []
        self.module_level_scripts = {}

    def set_use_requirements_txt(self, flag_value):
        self.use_requirements_txt = flag_value

    def set_freeze_requirements(self, value):
        if not value:
            self.freeze_requirements = False
            self.freeze_requirements_params = {}
        elif value is True:
            self.freeze_requirements = True
            self.freeze_requirements_params = {}
        else:
            self.freeze_requirements = True
            self.freeze_requirements_params = dict(value)

    def set_version_modules(self, module_paths):
        if isinstance(module_paths, basestring):
            module_paths = [module_paths]
        self.version_module_paths = list(module_paths)

    def set_module_level_scripts(self, script_names_to_module_names):
        self.module_level_scripts = script_names_to_module_names

    def setup(self, **kwargs):
        self._modify_setup_kwargs(kwargs)
        return setuptools.setup(**kwargs)

    def _modify_setup_kwargs(self, kwargs):
        script_file = sys.argv[0]
        if sys.argv[0].lower() != "setup.py":
            matching_manifest_template = os.path.splitext(script_file)[0] + ".MANIFEST.in"
            if os.path.exists(matching_manifest_template):
                self.cmd_opt_setdefault(kwargs, 'sdist', 'template', matching_manifest_template)

        if self.freeze_requirements:
            for key in ("pypi_server", "server_plugin"):
                if key in self.freeze_requirements_params:
                    self.cmd_opt_setdefault(kwargs, FreezeRequirementsCommand.SHORTNAME, key,
                                            self.freeze_requirements_params[key])

        if kwargs.get('version', None) is not None and self.version_module_paths:
            raise ValueError("when specifying version modules, you must not also specify hard-coded `version` in setup")
        if kwargs.get('version', None) is None and not self.version_module_paths:
            raise ValueError("you must either specify version modules or give a hard-coded `version` in setup")
        if self.version_module_paths:
            if is_packaging():
                # ignored, replaced later by the SetVersion command
                kwargs['version'] = "0.0.0"
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
                        script_name=script_file,
                        hook_module=hook_module,
                        func_name=func_name,
                    )
                    for (script_file, (_, hook_module, func_name)) in zip(
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
                # --
                SdistReplacement, EggInfoReplacement,
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


class SdistReplacement(setuptools_sdist):
    SHORTNAME = "sdist"

    def make_release_tree(self, base_dir, files):
        self.mkpath(base_dir)
        # alternative script locations are made possible
        script_file = sys.argv[0]
        if script_file.lower() != "setup.py":
            files = [f for f in files if f.lower() != "setup.py"]
            self.copy_file(script_file, os.path.join(base_dir, "setup.py"))
        if self.template is not None and self.template.lower() != "manifest.in":
            files = [f for f in files if f.lower() != "manifest.in"]
            self.copy_file(self.template, os.path.join(base_dir, "MANIFEST.in"))
        return setuptools_sdist.make_release_tree(self, base_dir, files)


class EggInfoReplacement(setuptools_egg_info):
    SHORTNAME = "egg_info"

    def find_sources(self):
        """Generate SOURCES.txt manifest file"""
        manifest_filename = os.path.join(self.egg_info, "SOURCES.txt")
        mm = manifest_maker(self.distribution)
        mm.manifest = manifest_filename
        # this line is our modification - the rest remains unchanged
        mm.template = self.get_finalized_command('sdist').template
        mm.run()
        self.filelist = mm.filelist
