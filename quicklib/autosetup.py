from .setupapi import _add_quicklib_commands


def setup_self_setup_commands(cmdclass, version_module_paths):
    _add_quicklib_commands(cmdclass, version_module_paths)
    from .incorporator import CreateIncorporatedZip
    cmdclass.update({
        CreateIncorporatedZip.SHORTNAME: CreateIncorporatedZip,
    })
