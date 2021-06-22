from __future__ import print_function
from ..py23.builtins import str
import os
import tempfile
from argparse import ArgumentParser, SUPPRESS
from datetime import datetime
from pprint import pprint

from piptools.locations import CACHE_DIR as DEFAULT_CACHE_DIR
from piptools.resolver import Resolver
from piptools.cache import DependencyCache
from piptools.repositories import PyPIRepository
from piptools._compat import parse_requirements

from .setupyml import SetupYml
from .quicklibsetup import create_package_from_kwargs
from ..versioning import GitVersionCalculator

TIMESTAMP_FORMAT = "%Y%m%dT%H%M%S"
HUMAN_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def create_lock_setup_kwargs(setup_yml, target_name, target_version, timestamp, concrete_reqs):
    setup_yml.set_env_var("human_timestamp", timestamp.strftime(HUMAN_TIMESTAMP_FORMAT))
    setup_yml.set_env_var("dateTtime", timestamp.strftime(TIMESTAMP_FORMAT))
    setup_yml.set_env_var("version", target_version)
    lock_kwargs = setup_yml.lock
    if lock_kwargs['name'] == target_name:
        raise ValueError("the locked library must be given a name different than its target")
    # we must not include any packages, so we explicitly set an empty list
    lock_kwargs['packages'] = []
    # TODO: support cases of extras, environmental markers etc
    # use exactly the concrete reqs list without any modifications
    lock_kwargs['install_requires'] = list(concrete_reqs)
    lock_kwargs['extras_require'] = {}
    lock_kwargs['use_requirements_txt'] = False
    print("creating locked-library with the following setup parameters:")
    pprint(lock_kwargs)
    return lock_kwargs


def make_concrete(reqs, pip_args=(), prereleases=False):
    tmp_repository = PyPIRepository(pip_args, DEFAULT_CACHE_DIR)
    tmp_file = tempfile.mktemp("-requirements.txt", "ql-lock-")
    open(tmp_file, "w").write("\n".join(reqs))
    try:
        constraints = list(parse_requirements(tmp_file, tmp_repository.session))
    finally:
        os.unlink(tmp_file)
    resolver = Resolver(
        constraints=constraints, repository=tmp_repository, cache=DependencyCache(DEFAULT_CACHE_DIR),
        clear_caches=True, prereleases=prereleases
    )
    concrete_reqs = resolver.resolve()
    simple_req_lines = [str(i.req) for i in concrete_reqs]
    return simple_req_lines


def main():
    parser = ArgumentParser(prog="quicklib-lock", description="package a locked library with frozen dependencies")
    parser.add_argument("-s", "--setup-yml", default="quicklib_setup.yml", help="setup YAML file (with a 'lock' entry)")
    parser.add_argument("--timestamp", metavar="<"+TIMESTAMP_FORMAT+">",
                        help="timestamp to put on library (default: current time)")
    parser.add_argument("--version", help="lock this specific version of your base library (default: git-based)")
    parser.add_argument("--pypi-index", metavar="url", help="optional alternate pypi index url")
    parser.add_argument("-f", "--find-links", action="append", dest="pip_find_links", metavar="url",
                        help="pip search flags (additional dirs/urls with packages)")
    parser.add_argument("--pre", action="store_true", help="allow pre-releases in resolution")
    parser.add_argument("--more-pip-args", help=SUPPRESS)
    args, args_for_setup_script = parser.parse_known_args()
    if not os.path.exists(args.setup_yml):
        parser.error("file '%s' not found" % args.setup_yml)
    if args.timestamp is None:
        timestamp = datetime.now()
    else:
        try:
            timestamp = datetime.strptime(args.timestamp, TIMESTAMP_FORMAT)
        except ValueError:
            parser.error("invalid timestamp '%s', should be formatted as %s" % (args.timestamp, TIMESTAMP_FORMAT))
    args.pip_args = []
    if args.pypi_index:
        args.pip_args.extend(["-i", args.pypi_index])
        if args.pypi_index.lower().startswith("http://"):
            args.pip_args.extend(["--trusted-host",
                                  args.pypi_index.split("://", 1)[1].split("/", 1)[0].split(":", 1)[0]])
    if args.pip_find_links:
        for url in args.pip_find_links:
            args.pip_args.extend(["--find-links", url])
    if args.more_pip_args:
        args.pip_args.extend(args.more_pip_args.split())

    setup_yml = SetupYml.load_from_file(args.setup_yml)

    target_name = setup_yml.lock.get("target", {}).get("name")
    if target_name is None:
        target_name = setup_yml.setup['name']
    if args.version is not None:
        target_version = args.version
    elif "version" in setup_yml.lock.get("target", {}):
        target_version = setup_yml.lock["target"]["version"]
    elif "version" in setup_yml.setup:
        target_version = setup_yml.setup["version"]
    else:
        target_version = GitVersionCalculator().getVersion()
    core_requirement = "%s==%s" % (target_name, target_version)

    concrete_reqs = make_concrete([core_requirement], args.pip_args, args.pre)
    lock_setup_kwargs = create_lock_setup_kwargs(setup_yml, target_name, target_version, timestamp, concrete_reqs)
    create_package_from_kwargs(lock_setup_kwargs, args_for_setup_script)


if __name__ == '__main__':
    main()
