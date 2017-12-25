import os
from setuptools import setup, find_packages

# TODO: in subdir-packaging, this is what is sometimes used instead of try-except:
# >> is_packaging = os.path.basename(sys.argv[0]) == "mylib_setup.py"

cmdclass = {}
version_module_path = os.path.join(os.path.dirname(__file__), "examplepackage", "version.py")

try:
    import quicklib
    # TODO: is_packaging = quicklib.is_packaging() ?
    is_packaging = True
except ImportError:
    is_packaging = False
    # TODO: maybe from setuptools import setup here?
else:
    # TODO: maybe from quicklib import setup?
    quicklib.setup_commands(cmdclass, [version_module_path])

version_load_vars = {}
execfile(version_module_path, version_load_vars)
version = version_load_vars['__version__']


# debug
import sys
with open("/Users/talila/yonatan/quicklib/examplelibrary/debug.txt", "a") as f:
    print >> f, "examplelibrary setup: is_packaging = %s, args = %s" % (is_packaging, sys.argv)


setup(
    # needed
    cmdclass=cmdclass,
    name='examplelibrary',
    version=version,
    url="https://example.com/",
    author='ACME Inc.',
    author_email='user@example.com',
    description='examplelibrary: a library to demonstrate how quicklib is used to quickly setup python libraries',
    license='Copyright ACME Inc.',
    # TODO: requirements are on the quicklib agenda
    install_requires=[],
    tests_require=[],
    packages=find_packages(),
    # package_data={'': ['*.suffix']},
    platforms='any',
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
