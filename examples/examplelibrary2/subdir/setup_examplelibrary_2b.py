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
    name='examplelibrary_2b',
    url="https://example.com/",
    author='ACME Inc.',
    author_email='user@example.com',
    description='examplelibrary (2b): a partial-content library built from non-default setup script in sub-directory',
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
        'b_only',
    ],
    version_module_paths=[
        "examplepackage2",
    ],
    module_level_scripts={
        'examplescript2b': 'examplepackage2.examplemodule2',
    },
)
