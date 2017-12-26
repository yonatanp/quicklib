import os
import sys

import setuptools

from .versioning import read_module_version


def is_packaging():
    return not os.path.exists("PKG-INFO")


def setup(**kwargs):
    version_module_paths = kwargs.pop('version_module_paths', None)

    version = kwargs.pop('version', None)
    if version_module_paths:
        if version is not None:
            raise ValueError("when specifying `version_module_paths`, you must not also specify hard-coded `version`")
        version = read_module_version(version_module_paths[0])
    else:
        if version is None:
            # TODO: auto-generated boilerplate
            raise ValueError("you must either specify `version_module_paths` or `version`")
    kwargs['version'] = version

    cmdclass = kwargs.pop('cmdclass', {})
    _add_quicklib_commands(cmdclass, version_module_paths)
    kwargs['cmdclass'] = cmdclass

    if 'packages' not in kwargs:
        packages = setuptools.find_packages()
        print "note: packages auto-discovered:"
        for p in packages:
            print "  - %s" % (p,)
        kwargs['packages'] = packages

    # # TODO: requirements are on the agenda
    # if 'install_requires' not in kwargs:
    #     pass

    script_args = []
    orig_script_args = kwargs.pop('script_args', sys.argv[1:])
    if is_packaging():
        script_args += ["clean_egg_info"]
        script_args += ["bundle_incorporated_zip"]
        if version_module_paths:
            script_args += ["version_set_by_git"]
        script_args += orig_script_args
        if version_module_paths:
            script_args += ["version_reset_to_dev"]
        script_args += ["clean_any_bundled_incorporated_zip"]
    else:
        script_args = orig_script_args
    kwargs["script_args"] = script_args

    return setuptools.setup(**kwargs)


def _add_quicklib_commands(cmdclass, version_modules=None):
    from .commands import CleanEggInfo
    from .versioning import VersionSetByGit, VersionResetToDev
    from .incorporator import BundleIncorporatedZip, CleanAnyBundledIncorporatedZip
    cmdclass.update({
        CleanEggInfo.SHORTNAME: CleanEggInfo,
        VersionSetByGit.SHORTNAME: VersionSetByGit.with_version_modules(version_modules),
        VersionResetToDev.SHORTNAME: VersionResetToDev.with_version_modules(version_modules),
        BundleIncorporatedZip.SHORTNAME: BundleIncorporatedZip,
        CleanAnyBundledIncorporatedZip.SHORTNAME: CleanAnyBundledIncorporatedZip,
    })


