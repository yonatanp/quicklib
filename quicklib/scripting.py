import os
import textwrap

from setuptools import Command
from distutils import log

from .virtualfiles import put_file


def create_script_hook_block():
    return textwrap.dedent("""
        import runpy


        def main():
            scripthook_name = __name__
            if not scripthook_name.endswith("__scripthook__"):
                raise Exception("this __scripthook__ module expects to run from a module whose name ends with __scripthook__")
            target_module_name = scripthook_name.rsplit("__scripthook__", 1)[0]
            runpy.run_module(target_module_name, run_name="__main__")
    """[1:-1])


class CreateScriptHooks(Command):
    SHORTNAME = "create_script_hooks"

    user_options = [
        ("script-modules=", None,
         "modules to attach scripthook sibling modules for making module-main console scripts")
    ]

    # TODO: this whole dance of placing the script hooks next to the script modules is not necessary.
    # TODO: instead, replace with a single top level (?) __script_hooks__ module with an individual function for each target module.

    # TODO: this may not always work, and assumes we're in the base folder, etc
    @classmethod
    def module_to_path(cls, module_name, where='.'):
        path = os.path.join(where, *module_name.split("."))
        if os.path.isdir(path):
            path = os.path.join(path, "__main__.py")
        else:
            path += ".py"
        if not os.path.exists(path):
            raise Exception("translated module '%s' to path '%s', but the path does not exist")
        if not os.path.isfile(path):
            raise Exception("translated module '%s' to path '%s', but the path is not a regular file")
        return path

    @classmethod
    def module_to_script_hook_path(cls, module_name):
        module_path = cls.module_to_path(module_name)
        root, ext = os.path.splitext(module_path)
        return "%s__scripthook__%s" % (root, ext)

    @classmethod
    def module_to_script_hook_module(cls, module_name):
        script_hook_path = cls.module_to_script_hook_path(module_name)
        # TODO: bah, this is backwards code
        return os.path.splitext(os.path.relpath(script_hook_path))[0].replace(os.path.sep, ".")

    def initialize_options(self):
        self.script_modules = None

    def finalize_options(self):
        if self.script_modules is None:
            self.script_modules = []
        elif isinstance(self.script_modules, basestring):
            self.script_modules = self.script_modules.split(",")
        if len(self.script_modules) != len(set(self.script_modules)):
            raise Exception("duplicated script modules requested: %s" % self.script_modules)
        if not self.script_modules:
            log.warn("warning: no script_modules provided, CreateScriptHooks command will have no effect")
        self.script_hook_paths = map(self.module_to_script_hook_path, self.script_modules)

    def run(self):
        for script_hook_path in self.script_hook_paths:
            put_file(script_hook_path, create_script_hook_block())
