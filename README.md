# quicklib

Build hassle-free setup scripts for your python libraries, with practical versioning, requirements specification, and more (to come).

## Installation

Install using:

    pip install quicklib

Or clone this repo and run:

    python setup.py install

## Creating libraries

### File structure

The recommended library file structure is something like:

````
mylibrary/
  |-- setup.py
  |-- README.md
  mypackage/
    |-- __init__.py
    |-- version.py
    |-- module1.py
    |-- module2.py
    |-- subpackage/
      |-- __init__.py
      |-- module3.py  
````

If you want to include more than one top-level package in your library, place additional ones next to `mypackage`.

For a deeper dive into recommended structure and other possible options, check out [Structuring Your Project](http://docs.python-guide.org/en/latest/writing/structure/) at the Hitchhiker's Guide to Python.

### Setup script

For an example `setup.py` file see [examplelibrary's setup.py](examplelibrary/setup.py).

The setup script must include this fixed stub copy-pasted verbatim:
````Python
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
````

After that, where you would usually call `setuptools.setup(...)`, call `quicklib.setup(...)` instead:
````Python
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
    version_module_paths=[
        os.path.join(os.path.dirname(__file__), "examplepackage", "version.py"),
    ],
)
````

Most parameters are exactly the same as they are in `setuptools`.

Additional parameters:
* `version_module_paths` - see details in "Versioning" below

Modified parameter defaults:
* if `packages` is not given, `find_packages()` is used automatically to discover packages under your library's top directory.

### Versioning

The build process automatically sets your library version based on the git log and tags. This version information is applied to the built library and can later be programatically queried by library package users.

#### version value inference

1. It `git-describe`s the `HEAD` searching for the latest annotated (!) tag with a `major.minor` label
2. If the tag is placed directly on the current `HEAD` then this is the version label
    * otherwise, a `.micro` suffix is added denoting the number of commits between the tag and `HEAD`
3. Finally, if there are any local modifications, a `.dirty` suffix is added

#### adding version info to your packages

Add a `version.py` stub file under any of your top-level packages with this fixed template:
````Python
# quicklib version boilerplate
DEV_VERSION = "0.0.0.dev0"
__version__ = DEV_VERSION
````

In addition, tell `setup.py` where to find those files:
````Python
    quicklib.setup(
        version_module_paths=[
            os.path.join(os.path.dirname(__file__), "mypackage", "version.py"),
            # ...
            # ... you can specify more than one
            # ...
        ],
    )
````

Then, your users can programtically query this version value by running e.g.:
````Python
    import mypackage
    print mypackage.version.__version__
````

#### versioning multiple packages

If your library contains multiple top-level packages, a `version.py` file should usually be added under each of them.
This allows your library users to ask about the version of each of your individual packages while being agnostic to the fact that they come from the same library.
If you find this confusing, you may want to stick to one top-level package per library.
