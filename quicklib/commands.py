import glob
import os
import shutil

from setuptools import Command
from distutils import log


class CleanEggInfo(Command):
    SHORTNAME = "clean_egg_info"

    description = "clean up *.egg-info leftovers from previous builds to avoid build errors (default in quicklib setup)"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # horrible setuptools can use a stale SOURCES.txt from egg-info folders
        egg_info_subdirs = list(map(os.path.abspath, glob.glob("*.egg-info")))
        for egg_info_subdir in egg_info_subdirs:
            log.info("Cleaning up egg_info directory %r..." % egg_info_subdir)
            shutil.rmtree(egg_info_subdir)


class ExportMetadata(Command):
    SHORTNAME = "export_metadata"

    description = "use this if you want to export metadata values (e.g. dynamically generated ones)"

    user_options = [
        ("write-version-file=", None,
         "path of file to be overwritten with the version calculated for this build"),
    ]

    def initialize_options(self):
        self.write_version_file = None

    def finalize_options(self):
        pass

    def run(self):
        self._writeVersionIfNeeded()

    def _writeVersionIfNeeded(self):
        if self.write_version_file:
            open(self.write_version_file, "w").write(str(self.distribution.metadata.version))
