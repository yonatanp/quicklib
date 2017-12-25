import glob
import os
import shutil

from setuptools import Command
from distutils import log


def setup_commands(cmdclass, version_modules):
    from .versioning import VersionSetByGit, VersionResetToDev
    cmdclass.update({
        CleanEggInfo.SHORTNAME: CleanEggInfo,
        VersionSetByGit.SHORTNAME: VersionSetByGit.with_version_modules(version_modules),
        VersionResetToDev.SHORTNAME: VersionResetToDev.with_version_modules(version_modules),
    })


# TODO: need initialize_options and finalize_options?
class CleanEggInfo(Command):
    SHORTNAME = "clean_egg_info"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # horrible setuptools can use a stale SOURCES.txt from egg-info folders
        egg_info_subdirs = map(os.path.abspath, glob.glob("*.egg-info"))
        for egg_info_subdir in egg_info_subdirs:
            log.info("Cleaning up egg_info directory %r..." % egg_info_subdir)
            shutil.rmtree(egg_info_subdir)
