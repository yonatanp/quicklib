from .setupapi import _add_quicklib_commands


def setup_self_setup_commands(cmdclass):
    _add_quicklib_commands(cmdclass)
    from .incorporator import CreateIncorporatedZip
    cmdclass.update({
        CreateIncorporatedZip.SHORTNAME: CreateIncorporatedZip,
    })
