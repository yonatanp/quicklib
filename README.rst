quicklib
========

Build hassle-free setup scripts for your python libraries, with
practical versioning, requirements specification, and more (to come).

Installation
------------

Install using:

::

    pip install quicklib

Or clone this project's `repo`_ and run:

::

    python setup.py install

Creating libraries
------------------

**TL;DR** - run ``python -m quicklib.bootstrap`` in a new folder and
answer some questions, and you're good to go coding. Look at
`examplelibrary`_ for an example created with this bootstrap process.

Also, your library needs to be in a git-managed folder, and needs at
least one numeric ``major.minor`` tag in your current history.

If you have no version tags yet, create the first one now and push it:

::

    git tag -a 0.1 -m "first version tag: 0.1"
    git push origin 0.1

File structure
~~~~~~~~~~~~~~

The recommended library file structure is something like:

::

    mylibrary/
      |----- setup.py
      |  | OR
      |  --- quicklib_setup.yml
      |-- README.md
      |-- [requirements.txt]
      mypackage/
        |-- __init__.py
        |-- version.py
        |-- module1.py
        |-- module2.py
        |-- subpackage/
          |-- __init__.py
          |-- module3.py

If you want to include more than one top-level package in your library,
place additional ones next to ``mypackage``.

For a deeper dive into recommended structure and other possible options,
check out `Structuring Your Project`_ at the Hitchhiker's Guide to
Python.

Setup script
~~~~~~~~~~~~

For an example ``setup.py`` file see `examplelibrary's setup.py`_.

The setup script must include this fixed stub copy-pasted verbatim:

.. code:: Python

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

After that, where you would usually call ``setuptools.setup(...)``, call
``quicklib.setup(...)`` instead:

.. code:: Python

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
            "examplepackage/version.py",
        ],
    )

Most parameters are exactly the same as they are in ``setuptools``.

Additional parameters:

-  ``version_module_paths`` - see details in "Versioning" below

Modified parameter defaults:

-  if ``packages`` is not given, ``find_packages()`` is used
   automatically to discover packages under your library's top
   directory.

YAML-based setup
~~~~~~~~~~~~~~~~

The easiest way for simple libraries is to provide all necessary details
in a YAML file. This is essentially the same as creating a setup.py that
uses the YAML dictionary as its kwargs.

For example, create a ``quicklib_setup.yml`` file at the root of your
project:

::

    setup:
      name: mylibrary
      description: a library for doing some stuff
      version: 1.0

And run ``quicklib-setup sdist`` (instead of ``python setup.py sdist``)
to create the library package.

You can also ``include`` additional files of a similar format (overriding each other in order of appearance), e.g. to use as common template of values:

::

    # mylib_setup.yml
    include:
        - ../common_properties.yml
    setup:
        name: mylibrary

    # common_properties.yml
    setup:
        author: ACME Inc.
        author_email: user@example.com

For additional parameters, see the rest of this documentation and
provide parameters to ``quicklib.setup(...)`` as values under the
``setup`` dictionary in your ``quicklib_setup.yml`` file.

Take a look at the `minimal example library`_ for usage example.

Setup script in non-standard location
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to build libraries with quicklib from setup scripts
other than "top level setup.py". This allows building more than one
library (or variants of a single library) from a single repository.

Look at `examplelibrary2`_ for two such example library variants built
from the same sources.

Just place your setup code in any folder and run it the same way as
usual, e.g.:

::

    python my_other_setup.py sdist bdist_wheel

Note that if you want to have a ``MANIFEST.in`` file to go with the
script, you can put it alongside it and using the same base name,
e.g.:

::

    ...
    |-- my_other_setup.py
    |-- my_other_setup.MANIFEST.in
    ...

If no such alternative MANIFEST.in file is present and a top-level
MANIFEST.in exists, it will be used as usual.

Versioning
~~~~~~~~~~

The build process automatically sets your library version based on the
git log and tags. This version information is applied to the built
library and can later be programmatically queried by library package
users.

version value inference
^^^^^^^^^^^^^^^^^^^^^^^

1. It ``git-describe``\ s the ``HEAD`` searching for the latest
   annotated (!) tag with a ``major.minor`` label
2. If the tag is placed directly on the current ``HEAD`` then this is
   the version label

   -  otherwise, a ``.micro`` suffix is added denoting the number of
      commits between the tag and ``HEAD``

3. Finally, if there are any local modifications, a ``.dirty`` suffix is
   added

adding version info to your packages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add a ``version.py`` stub file under any of your top-level packages with
this fixed template:

.. code:: Python

    # quicklib version boilerplate
    DEV_VERSION = "0.0.0.dev0"
    __version__ = DEV_VERSION

In addition, tell ``setup.py`` where to find those files:

.. code:: Python

        quicklib.setup(
            version_module_paths=[
                "mypackage/version.py",
                # ... you can specify more than one
            ],
        )

Then, your users can programmatically query this version value by running
e.g.:

.. code:: Python

        import mypackage
        print(mypackage.version.__version__)

versioning multiple packages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your library contains multiple top-level packages, a ``version.py``
file should usually be added under each of them. This allows your
library users to ask about the version of each of your individual
packages while being agnostic to the fact that they come from the same
library. If you find this confusing, you may want to stick to one
top-level package per library.

Choosing packages to include
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The default behavior calls ``setuptools.find_packages()`` and typically collects all top-level packages found. To disable this behavior, provide ``packages`` yourself.

Another alternative is to provide a list of top-level package names in the ``top_packages`` argument. In this case, ``find_packages()`` is called when only these top-level packages are included in the search.

Requirements
~~~~~~~~~~~~

To add requirements to your library, add them in a ``requirements.txt``
file at the project root.

Use syntax such as:

::

    numpy
    pandas==0.18.1
    yarg~=0.1.1

Freezing requirements
^^^^^^^^^^^^^^^^^^^^^

Sometimes you want to hardcode the versions of your dependencies. This
helps provide your users the exact same configuration you built and
tested with. To avoid having to manually update those numbers, you can
keep your requirements specified as usual but activate "requirement
freezing".

Do this by passing ``freeze_requirements=True`` to the
``quicklib.setup(...)`` call in ``setup.py``. At packaging time, the
available versions will be retrieved from ``pypi.python.org``, and the
latest matching version will be hardcoded as the requirement.

Note: if your library depends on a hardcoded ``dep==1.0`` but ``dep``
did not hardcode its dependencies, your users might get different
packages. To get around that you can specify your requirements'
requirements as your own requirements. Automatically fetching this
information is on this library's roadmap.

.. _when-not-using-pypipythonorg:

when not using pypi.python.org
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your dependency libraries come from another package repository, you
can specify another address or even provide your own plugin to retrieve
information from such a server.

To do this, provide a dictionary of options in ``freeze_requirements``:

.. code:: Python

        quicklib.setup(
            # ...
            freeze_requirements = {
                # alternative pypi server address
                'pypi_server': 'https://my-private-pypi.com/packages/',
                # when given, this is imported at packaging time and used to find package versions.
                # see quicklib/requirements.py for the StandardPypiServerPlugin default plugin, and follow its interface.
                'server_plugin': 'foo.bar:baz()',
            }
        )

.. _repo: https://github.com/yonatanp/quicklib
.. _examplelibrary: https://github.com/yonatanp/quicklib/tree/master/examples/examplelibrary/
.. _minimal example library: https://github.com/yonatanp/quicklib/tree/master/examples/minimal/
.. _examplelibrary2: https://github.com/yonatanp/quicklib/tree/master/examples/examplelibrary2/
.. _Structuring Your Project: http://docs.python-guide.org/en/latest/writing/structure/
.. _examplelibrary's setup.py: https://github.com/yonatanp/quicklib/tree/master/examples/examplelibrary/setup.py
