import os
import textwrap
from argparse import ArgumentParser
from distutils.core import run_setup

import yaml

from . import incorporator

TEMP_SETUP_FILE_PATH = "quicklib_setup_from_yml.py"


def load_setup_from_yml(yml_path):
    yml_document = yaml.load(open(yml_path, "r"))
    setup_kwargs = load_includes(yml_document.get('include', ()), os.path.dirname(yml_path))
    setup_kwargs.update(yml_document.get('setup', {}))
    return setup_kwargs


def load_includes(include_strings, base_dir):
    layered_dict = {}
    for include_string in include_strings:
        include_string = os.path.expanduser(include_string)
        include_path = os.path.join(base_dir, include_string)
        layered_dict.update(load_setup_from_yml(include_path))
    return layered_dict


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
    parser.add_argument("--setup-yml", default="quicklib_setup.yml", help="setup YAML file")
    args, args_for_setup_script = parser.parse_known_args()
    setup_kwargs = load_setup_from_yml(args.setup_yml)
    create_package_from_kwargs(setup_kwargs, args_for_setup_script)
