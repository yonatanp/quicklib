import os

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
        ("persistent-filename=", None,
         "where calculated requirements are saved, and later loaded back")
    ]

    def initialize_options(self):
        self.persistent_filename = "dynamic_requirements.txt"

    def finalize_options(self):
        pass

    def run_packaging(self):
        pmi = self.get_finalized_command(PrepareManifestIn.SHORTNAME)
        pmi.rewriter.add_include(self.persistent_filename)
        log.info("persisting dynamic install_requires: %s" % (self.distribution.install_requires,))
        put_file(self.persistent_filename, "\n".join(self.distribution.install_requires))

    def run_deploying(self):
        self.distribution.install_requires = open(self.persistent_filename, "r").read().split("\n")
        log.info("loaded pre-persisted dynamic install_requires: %s" % (self.distribution.install_requires,))

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
         "alternative pypi server")
    ]

    def initialize_options(self):
        self.pypi_server = None

    def finalize_options(self):
        pass

    def run(self):
        frozen_requirements = [
            self.get_frozen_package_spec(item)
            for item in self.distribution.install_requires
        ]
        self.distribution.install_requires = frozen_requirements

    def get_frozen_package_spec(self, requirement_line):
        # imported here so that it's only needed in packaging time
        import yarg
        req = Requirement.parse(requirement_line)
        yarg_kw = {}
        if self.pypi_server is not None:
            yarg_kw['pypi_server'] = self.pypi_server
        available_versions = yarg.get(req.name, **yarg_kw).release_ids
        if not available_versions:
            raise Exception("no versions found for package %s" % req.name)
        matching_versions = [v for v in available_versions if v in req]
        if not matching_versions:
            raise Exception("no versions found for package %s matching %s" % (req.name, requirement_line))
        latest_version = matching_versions[-1]
        return "%s==%s" % (req.name, latest_version)


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
            if os.path.exists("requirements.txt"):
                self.requirements_txt = ["requirements.txt"]
            else:
                self.requirements_txt = []
        elif isinstance(self.requirements_txt, basestring):
            self.requirements_txt = self.requirements_txt.split(",")

    def run(self):
        for fn in self.requirements_txt:
            self.distribution.install_requires.extend(
                map(str, parse_requirements(open(fn, "r").read()))
            )
