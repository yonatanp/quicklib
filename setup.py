# caveat emptor: this is quicklib's own setup.py.
# it is NOT an example of how to write a setup.py that USES quicklib.
# if you're looking for an example, look at `examplelibrary/setup.py`.
import os
from setuptools import setup, find_packages

cmdclass = {}
version_module_path = os.path.join(os.path.dirname(__file__), "quicklib", "version.py")

is_packaging = not os.path.exists("PKG-INFO")
if is_packaging:
    import quicklib.autosetup
    quicklib.autosetup.setup_self_setup_commands(cmdclass)
    version = None
else:
    import quicklib
    version = quicklib.read_module_version(version_module_path)

setup(
    cmdclass=cmdclass,
    name='quicklib',
    version=version,
    url="https://github.com/yonatanp/quicklib",
    author='Yonatan Perry',
    author_email='yonatan.perry@gmail.com',
    description='quicklib: a library for helping with setup of python libraries',
    license='MIT',
    install_requires=[],
    tests_require=[],
    packages=find_packages(),
    package_data={'quicklib': ['quicklib_incorporated.zip']},
    platforms='any',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Operating System :: OS Independent',
    ],
    command_options={
        'version_set_by_git': {'version_module_paths': ('setup.py', version_module_path)},
    }
)
