import os
import textwrap
from argparse import ArgumentParser
from distutils.core import run_setup

from .. import incorporator
from .setupyml import SetupYml

TEMP_SETUP_FILE_PATH = "quicklib_setup_from_yml.py"


def create_package_from_kwargs(ql_setup_kwargs, args_for_setup_script):
    virtual_setup_py_code = textwrap.dedent("""\
        %(bootstrap_block)s

        ql_setup_kwargs = %(ql_setup_kwargs)r    

        quicklib.setup(
            **ql_setup_kwargs
        )
    """) % dict(
        bootstrap_block=incorporator.create_bootstrap_block(),
        ql_setup_kwargs=ql_setup_kwargs,
    )

    try:
        open(TEMP_SETUP_FILE_PATH, "w").write(virtual_setup_py_code)
        run_setup(TEMP_SETUP_FILE_PATH, script_args=args_for_setup_script)
    finally:
        if os.path.exists(TEMP_SETUP_FILE_PATH):
            os.remove(TEMP_SETUP_FILE_PATH)


def main():
    parser = ArgumentParser(prog="quicklib-setup", description="package a library from a YAML file")
    parser.add_argument("-s", "--setup-yml", default="quicklib_setup.yml", help="setup YAML file")
    args, args_for_setup_script = parser.parse_known_args()
    if not os.path.exists(args.setup_yml):
        parser.error("file '%s' not found" % args.setup_yml)
    setup_yml = SetupYml.load_from_file(args.setup_yml)
    create_package_from_kwargs(setup_yml.setup, args_for_setup_script)


if __name__ == '__main__':
    main()
