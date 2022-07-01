import os
import re
import shutil
import textwrap
import zipfile

import pkg_resources
from setuptools import Command
from distutils import log

import quicklib
import quicklib.version
from .versioning import DEV_VERSION
from .virtualfiles import register_for_removal
from .datafiles import PrepareManifestIn

INCORPORATED = 'quicklib_incorporated'
INCORPORATED_ZIP = INCORPORATED + '.zip'


# ---- used by quicklib itself

class CreateIncorporatedZip(Command):
    SHORTNAME = "create_incorporated_zip"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import quicklib
        quicklib_path = os.path.relpath(os.path.dirname(quicklib.__file__), os.getcwd())
        final_path = os.path.join(quicklib_path, INCORPORATED_ZIP)
        log.info("incorporating %s from %s (and from select dependencies)" % (INCORPORATED_ZIP, os.path.abspath(quicklib_path)))
        self.create_zip(final_path)
        register_for_removal(final_path)

    def create_zip(self, target_path, excluded_exts=(".pyc", ".pyo"), excluded_dirs=('__pycache__',)):
        packages = self._pacakges_to_incorporate()
        top_level_folders = [os.path.dirname(pkg.__file__) for pkg in packages]
        with zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for top_folder in top_level_folders:
                for root, dirs, files in os.walk(top_folder):
                    if root in excluded_dirs:
                        continue
                    for f in files:
                        source_file = os.path.join(root, f)
                        arcname = os.path.relpath(source_file, os.path.dirname(top_folder))
                        if os.path.splitext(source_file)[-1].lower() not in excluded_exts:
                            zipf.write(source_file, arcname)

    def _pacakges_to_incorporate(self):
        import quicklib
        return [quicklib]


def create_bootstrap_block():
    return textwrap.dedent("""
        # -------- quicklib direct/bundled import, copy pasted --------------------------------------------
        import sys as _sys, glob as _glob, os as _os
        is_packaging = not _os.path.exists("PKG-INFO")
        if is_packaging:
            import quicklib
        else:
            zips = _glob.glob("quicklib_incorporated.*.zip")
            if len(zips) != 1:
                raise Exception("expected exactly one incorporated quicklib zip but found %s" % (zips,))
            _sys.path.insert(0, zips[0]); import quicklib; _sys.path.pop(0)
        # -------------------------------------------------------------------------------------------------
        """)[1:-1]


# ---- used by setup process of libraries built using quicklib

class BundleIncorporatedZip(Command):
    SHORTNAME = "bundle_incorporated_zip"

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        version = quicklib.version.__version__
        if version == DEV_VERSION:
            raise Exception("cowardly refusing to bundle incorportated zip when quicklib states DEV_VERSION "
                            "(path to quicklib is %s, did you remember to pip install and use that?)" %
                            os.path.dirname(os.path.abspath(quicklib.__file__)))
        zip_path = pkg_resources.resource_filename('quicklib', INCORPORATED_ZIP)
        bundled_zip_name = "%s.v%s.zip" % (INCORPORATED, version)
        log.info("bundling %s as %s" % (
            zip_path, bundled_zip_name))
        shutil.copy(zip_path, bundled_zip_name)
        register_for_removal(bundled_zip_name)
        # add to MANIFEST.in
        pmi = self.get_finalized_command(PrepareManifestIn.SHORTNAME)
        pmi.rewriter.add_include(bundled_zip_name)


# this tells the library whether it's using a fresh (source tree) or incorporated (zip) quicklib
def is_quicklib_incorporated():
    return bool(re.match("^%s\\.v.*\\.zip$" % INCORPORATED, os.path.dirname(os.path.dirname(quicklib.__file__))))
