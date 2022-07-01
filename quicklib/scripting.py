import os
import textwrap

from setuptools import Command
from distutils import log

from .virtualfiles import put_file


class CreateScriptHooks(Command):
    SHORTNAME = "create_script_hooks"

    user_options = [
        ("script-modules=", None,
         "modules for which a script-hook trampoline should be created for making module-main console scripts")
    ]

    def initialize_options(self):
        self.script_modules = None

    def finalize_options(self):
        if self.script_modules is None:
            self.script_modules = []
        elif isinstance(self.script_modules, str):
            self.script_modules = self.script_modules.split(",")
        if not self.script_modules:
            log.warn("warning: no script_modules provided, CreateScriptHooks command will have no effect")
        self.hook_modules = self._prepare_hook_modules()

    def _prepare_hook_modules(self):
        hook_module_path_to_functions = {}
        for target_module, hook_module, func_name in \
                self.target_module_names_to_hook_module_and_func_name(self.script_modules):
            hook_module_path = os.path.join(*hook_module.split(".")) + ".py"
            hook_module_path_to_functions.setdefault(hook_module_path, {})[func_name] = target_module
        return {
            hook_module_path: self.create_script_hooks_module_text(functions)
            for hook_module_path, functions in hook_module_path_to_functions.items()
        }

    # must be translated as one, since we include the index;
    # we include the index to support repeating modules and avoid naming ambiguities.
    @classmethod
    def target_module_names_to_hook_module_and_func_name(cls, module_names):
        result = []
        for index, module_name in enumerate(module_names):
            top_package = module_name.split(".", 1)[0]
            if not os.path.isdir(top_package):
                raise Exception("cannot create script hook for %s: only modules under top packages are supported, and "
                                "its top package %s doesn't seem to exist as code package" % (module_name, top_package))
            hook_module = "%s.__scripthooks__" % top_package
            func_name = "%s_%d" % (module_name.replace(".", "_"), index)
            result.append((module_name, hook_module, func_name))
        return result


    @classmethod
    def create_script_hooks_module_text(cls, functions):
        prefix = textwrap.dedent("""
            import runpy
        
        """[1:-1])
        function_template = textwrap.dedent("""
        
            def %(func_name)s():
                runpy.run_module("%(target_module_name)s", run_name="__main__")
        """[1:-1])
        return prefix + "".join([
            function_template % dict(
                func_name=func_name, target_module_name=target_module_name,
            )
            for func_name, target_module_name in functions.items()
        ])

    def run(self):
        for hook_module_path, script_content in self.hook_modules.items():
            put_file(hook_module_path, script_content)
