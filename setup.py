# WARNING: this is quicklib's own setup.py.
# it is NOT an example of how to write a setup.py that USES quicklib.
# if you're looking for an example, look at `examplelibrary/setup.py`.
import os
import sys
from setuptools import setup, find_packages

cmdclass = {}
version_module_path = os.path.join(os.path.dirname(__file__), "quicklib", "version.py")

is_packaging = not os.path.exists("PKG-INFO")
if is_packaging:
    from quicklib.setupapi import SetupModifier
    from quicklib.incorporator import CreateIncorporatedZip
    from quicklib.virtualfiles import UndoVirtualFiles
    cmdclass.update(SetupModifier.get_quicklib_commands())
    cmdclass.update({
        CreateIncorporatedZip.SHORTNAME: CreateIncorporatedZip,
        UndoVirtualFiles.SHORTNAME: UndoVirtualFiles,
    })
    version = None
else:
    import quicklib
    version = quicklib.read_module_version(version_module_path)

long_description = open("README.rst", "r").read()

script_args = sys.argv[1:]
if is_packaging:
    script_args = (
        ["clean_egg_info", "version_set_by_git", "create_incorporated_zip"] +
        script_args +
        ["undo_virtual_files"]
    )

setup(
    name='quicklib',
    version=version,
    url="https://github.com/yonatanp/quicklib",
    author='Yonatan Perry',
    author_email='yonatan.perry@gmail.com',
    description='quicklib: hassle-free setup scripts for your python libraries',
    long_description=long_description,
    license='MIT',
    install_requires=[
        'yarg~=0.1.9',
        'PyYAML>=4.2b1',
    ],
    tests_require=[],
    python_requires=">=3.7",
    packages=find_packages(),
    package_data={'quicklib': ['quicklib_incorporated.zip']},
    platforms='any',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Operating System :: OS Independent',
    ],
    zip_safe=False,
    cmdclass=cmdclass,
    script_args=script_args,
    command_options={
        'version_set_by_git': {'version_module_paths': ('setup.py', version_module_path)},
    },
    entry_points={
        'console_scripts': [
            'quicklib-setup = quicklib.cli.quicklibsetup:main',
            # utilities
            'quicklib-get-git-version = quicklib.versioning:calculate_git_version',
        ],
    },
)
