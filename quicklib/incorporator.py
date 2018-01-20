import os
import re
import shutil
import textwrap

import pkg_resources
from setuptools import Command
from distutils import log

import quicklib
import quicklib.version
from .versioning import DEV_VERSION
from .virtualfiles import register_for_removal
from .datafiles import PrepareManifestIn

QL_INCORPORATED = 'quicklib_incorporated'
QL_INCORPORATED_ZIP = QL_INCORPORATED + '.zip'


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
        temp_path = os.path.join(os.path.dirname(quicklib_path), QL_INCORPORATED_ZIP)
        final_path = os.path.join(quicklib_path, QL_INCORPORATED_ZIP)
        log.info("incorporating %s from %s" % (QL_INCORPORATED_ZIP, os.path.abspath(quicklib_path)))
        self.zip(quicklib_path, temp_path)
        shutil.move(temp_path, final_path)
        register_for_removal(final_path)

    def zip(self, source_path, target_path):
        # python equivalent of: zip -r quicklib_incorporated.zip quicklib -i '*.py'
        import zipfile
        with zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_path):
                for f in files:
                    if os.path.splitext(f)[-1].lower() == ".py":
                        zipf.write(os.path.join(root, f))


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
        zip_path = pkg_resources.resource_filename('quicklib', QL_INCORPORATED_ZIP)
        bundled_zip_name = "%s.v%s.zip" % (QL_INCORPORATED, version)
        log.info("bundling %s as %s" % (
            zip_path, bundled_zip_name))
        shutil.copy(zip_path, bundled_zip_name)
        register_for_removal(bundled_zip_name)
        # add to MANIFEST.in
        pmi = self.get_finalized_command(PrepareManifestIn.SHORTNAME)
        pmi.rewriter.add_include(bundled_zip_name)


# this tells the library whether it's using a fresh (source tree) or incorporated (zip) quicklib
def is_quicklib_incorporated():
    return bool(re.match("^%s\\.v.*\\.zip$" % QL_INCORPORATED, os.path.dirname(os.path.dirname(quicklib.__file__))))
