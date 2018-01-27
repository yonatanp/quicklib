import os
from collections import defaultdict


class SetupYml(object):
    def __init__(self, data_dict=None):
        if data_dict is None:
            data_dict = {}
        self._setup = data_dict.get('setup', {})
        self._lock = data_dict.get('lock', {})
        self._env = {}

    def set_env_var(self, name, value):
        self._env[name] = value

    def overlay(self, another):
        self._setup.update(another._setup)
        self._lock.update(another._lock)

    @property
    def setup(self):
        return self._setup.copy()

    @property
    def lock(self):
        result = {}
        lock = self._lock.copy()
        if "_template" in lock:
            # apply template things
            kwparams = defaultdict(lambda: "undefined")
            kwparams.update(self._setup)
            kwparams.update(self._env)
            for key, expr in lock['_template'].iteritems():
                result[key] = expr % kwparams
            del lock['_template']
        result.update(lock)
        return result

    @classmethod
    def load_from_file(cls, yml_path):
        import yaml
        yml_document = yaml.load(open(yml_path, "r"))
        result = SetupYml()
        result.overlay(
            cls.load_includes(yml_document.get('include', ()), os.path.dirname(yml_path))
        )
        result.overlay(SetupYml(yml_document))
        return result

    @classmethod
    def load_includes(cls, include_strings, base_dir):
        result = SetupYml()
        for include_string in include_strings:
            include_string = os.path.expanduser(include_string)
            include_path = os.path.join(base_dir, include_string)
            result.overlay(SetupYml.load_from_file(include_path))
        return result
