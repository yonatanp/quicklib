import os
import re
import sys

from setuptools import Command
from distutils import log
from pkg_resources import Requirement, parse_requirements

from .utils import is_packaging
from .virtualfiles import put_file
from .datafiles import PrepareManifestIn


class DynamicRequirementsCommand(Command):
    SHORTNAME = "dynamic_requirements"

    description = "persist dynamically manipulated distribution install-requirements into a file during packaging"

    user_options = [
        ("filename-install-requires=", None,
         "where calculated 'install_requires' values are saved, and later loaded back"),
        ("filename-extras-require=", None,
         "where calculated 'extras_require' values are saved, and later loaded back"),
    ]

    def initialize_options(self):
        self.filename_install_requires = "dynamic_install_requires.txt"
        self.filename_extras_require = "dynamic_extras_require.txt"

    def finalize_options(self):
        pass

    def run_packaging(self):
        pmi = self.get_finalized_command(PrepareManifestIn.SHORTNAME)

        pmi.rewriter.add_include(self.filename_install_requires)
        dumped_install_requires = repr(self.distribution.install_requires)
        log.info("persisting dynamic install_requires:\n%s" % dumped_install_requires)
        put_file(self.filename_install_requires, dumped_install_requires)

        pmi.rewriter.add_include(self.filename_extras_require)
        dumped_extras_require = repr(self.distribution.extras_require)
        log.info("persisting dynamic extras_require:\n%s" % dumped_extras_require)
        put_file(self.filename_extras_require, dumped_extras_require)

    def run_deploying(self):
        loaded_install_requires = open(self.filename_install_requires, "r").read()
        log.info("loaded pre-persisted dynamic install_requires:\n%s" % loaded_install_requires)
        self.distribution.install_requires = eval(loaded_install_requires)

        loaded_extras_require = open(self.filename_extras_require, "r").read()
        log.info("loaded pre-persisted dynamic extras_require:\n%s" % loaded_extras_require)
        self.distribution.extras_require = eval(loaded_extras_require)

    def run(self):
        if is_packaging():
            self.run_packaging()
        else:
            self.run_deploying()


class FreezeRequirementsCommand(Command):
    SHORTNAME = "freeze_requirements"

    description = "resolve latest package matching each requirement, resulting in hardcoded pkg==ver requirements"

    user_options = [
        ("pypi-server=", None,
         "alternative pypi server (when using a plugin, arbitrary data can be passed, depending on the plugin)"),
        ("server-plugin=", None,
         "external plugin for accessing pypi server and recovering package data"),
    ]

    def initialize_options(self):
        self.pypi_server = None
        self.server_plugin = 'quicklib.requirements:StandardPypiServerPlugin'

    def finalize_options(self):
        # giving a string spec for the external plugin helps when it depends on a package available only when packaging
        if isinstance(self.server_plugin, str):
            self.server_plugin = self._load_plugin_from_spec()

    PLUGIN_IMPORT_SPEC = "^([0-9a-zA-Z_.]+)(?::([0-9a-zA-Z_]+)(\\(\\))?)?$"

    def _load_plugin_from_spec(self):
        # import the module or the name from the module, and init if parentheses are given
        m = re.match(self.PLUGIN_IMPORT_SPEC, self.server_plugin)
        if not m:
            raise ValueError("invalid plugin import spec given: %s" % self.server_plugin)
        log.info("loading requirements plugin from %s" % self.server_plugin)
        module_name, member_name, should_invoke = m.groups()
        exec_globals = {}
        import_command = (
            "from %s import %s as plugin" % (module_name, member_name) if member_name else
            "import %s as plugin" % module_name
        )
        exec(import_command, exec_globals)
        plugin = exec_globals['plugin']
        if should_invoke:
            plugin = plugin()
        return plugin

    def run(self):
        frozen_requirements = [
            self.get_frozen_package_spec(item)
            for item in self.distribution.install_requires
        ]
        self.distribution.install_requires = frozen_requirements
        frozen_extras_require = {
            extra_cond: [
                self.get_frozen_package_spec(item)
                for item in req_list
            ]
            for extra_cond, req_list in self.distribution.extras_require.items()
        }
        self.distribution.extras_require = frozen_extras_require

    def get_frozen_package_spec(self, requirement_line):
        req = Requirement.parse(requirement_line)
        try:
            available_versions = self.server_plugin.get_ordered_package_versions(req.name, self.pypi_server)
        except Exception:
            log.error("freeze requirements: failed fetching available versions for %s" % req.name)
            raise
        if not available_versions:
            raise Exception("no versions found for package %s" % req.name)
        matching_versions = [v for v in available_versions if v in req]
        if not matching_versions:
            raise Exception("no versions found for package %s matching %s" % (req.name, requirement_line))
        latest_version = matching_versions[-1]
        self.set_req_version_specifier(req, latest_version)
        return str(req)

    @staticmethod
    def set_req_version_specifier(req, specific_version):
        req.specifier = Requirement.parse("dummy==%s" % specific_version).specifier


class StandardPypiServerPlugin:
    @staticmethod
    def get_ordered_package_versions(package_name, pypi_server=None):
        # imported here so that it's only needed in packaging time
        import yarg
        yarg_kw = {}
        if pypi_server is not None:
            yarg_kw['pypi_server'] = pypi_server
        available_versions = yarg.get(package_name, **yarg_kw).release_ids
        return available_versions


class UseRequirementsTxtCommand(Command):
    SHORTNAME = "use_requirements_txt"

    description = "incorporate requirements found in one or more 'requirements.txt' files"

    user_options = [
        ("requirements-txt=", None,
         "one or more requirements.txt (pip style) files")
    ]

    def initialize_options(self):
        self.requirements_txt = None

    def finalize_options(self):
        if self.requirements_txt is None:
            default_requirements_txt = os.path.join(os.path.dirname(sys.argv[0]), "requirements.txt")
            if os.path.exists(default_requirements_txt):
                self.requirements_txt = [default_requirements_txt]
            else:
                self.requirements_txt = []
        elif isinstance(self.requirements_txt, str):
            self.requirements_txt = self.requirements_txt.split(",")

    def run(self):
        for fn in self.requirements_txt:
            self.distribution.install_requires.extend(
                map(str, parse_requirements(open(fn, "r").read()))
            )
