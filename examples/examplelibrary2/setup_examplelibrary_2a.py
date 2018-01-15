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


quicklib.setup(
    name='examplelibrary_2a',
    url="https://example.com/",
    author='ACME Inc.',
    author_email='user@example.com',
    description='examplelibrary (2a): a partial-content library built from non-default setup script at top level',
    license='Copyright ACME Inc.',
    platforms='any',
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=[
        'examplepackage2',
        'a_only',
    ],
    version_module_paths=[
        "examplepackage2",
    ],
    module_level_scripts={
        'examplescript2a': 'examplepackage2.examplemodule2',
    },
)
