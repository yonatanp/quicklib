import os


# -------- quicklib direct/bundled import, copy pasted --------------------------------------------
import sys as _sys, glob as _glob
is_packaging = not os.path.exists("PKG-INFO")
if is_packaging:
    import quicklib
else:
    zips = _glob.glob("quicklib_incorporated.*.zip")
    if len(zips) != 1:
        raise Exception("expected exactly one incorporated quicklib zip but found %s" % (zips,))
    _sys.path.insert(0, zips[0]); import quicklib; _sys.path.pop(0)
# -------------------------------------------------------------------------------------------------


quicklib.setup(
    name='examplelibrary',
    url="https://example.com/",
    author='ACME Inc.',
    author_email='user@example.com',
    description='examplelibrary: a library to demonstrate how quicklib is used to quickly setup python libraries',
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
    freeze_requirements=True,
    version_module_paths=[
        os.path.join(os.path.dirname(__file__), "examplepackage", "version.py"),
    ],
    module_level_scripts={
        'examplescript': 'examplepackage.examplescript',
    },
)
