import os
from collections import defaultdict


class SetupYml:
    def __init__(self, data_dict=None):
        if data_dict is None:
            data_dict = {}
        self._setup = data_dict.get('setup', {})
        self._env = {}

    def set_env_var(self, name, value):
        self._env[name] = value

    def overlay(self, another):
        self._overlay_dict(self._setup, another._setup)

    def _overlay_dict(self, one, another):
        cumulative_dict_keys = ['_template']
        another = another.copy()
        for k in cumulative_dict_keys:
            if k in another:
                one.setdefault(k, {}).update(another.pop(k))
        one.update(another)

    @property
    def setup(self):
        return self._setup.copy()

    @classmethod
    def load_from_file(cls, yml_path):
        import yaml
        yml_document = yaml.safe_load(open(yml_path, "r"))
        result = SetupYml()
        result.overlay(
            cls.load_includes(yml_document.get('include', ()), os.path.dirname(yml_path))
        )
        result.overlay(SetupYml(yml_document))
        return result

    @classmethod
    def load_includes(cls, include_expressions, base_dir):
        result = SetupYml()
        for include_expr in include_expressions:
            if isinstance(include_expr, str):
                include_path = os.path.expanduser(include_expr)
                include_path = os.path.join(base_dir, include_path)
                included_setup_yml = SetupYml.load_from_file(include_path)
            elif isinstance(include_expr, dict):
                if "from" in include_expr and "import" in include_expr:
                    exec_globals = {}
                    exec("from %(from)s import %(import)s as imported_dict" % include_expr, exec_globals)
                    imported_dict = exec_globals['imported_dict']
                    if isinstance(imported_dict, SetupYml):
                        included_setup_yml = imported_dict
                    else:
                        included_setup_yml = SetupYml(data_dict=imported_dict)
                else:
                    raise ValueError("malformatted dict include: %r" % (include_expr,))
            else:
                raise TypeError("malformatted include: %r" % (include_expr,))
            result.overlay(included_setup_yml)
        return result
