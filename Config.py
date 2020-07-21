import json
import os

class Config:
    configs = {}

    def __init__(self, path, default_config=None, load_logging=False):
        self.path = path
        self.verbose = load_logging
        self.__default = default_config
        if path not in self.configs:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        self.configs[path] = json.load(f)
                        if self.verbose:
                            print(f"reading config: {self.configs[self.path]}")
                except:
                    with open(path, "a") as f:
                        self.configs[path] = default_config
                        json.dump(self.configs[path], f)
                        if self.verbose:
                            print("error reading config, using default:", default_config)
                for key in default_config:  # Allows newer versions of configs to add properties
                    if key not in self.configs[path]:
                        if self.verbose:
                            print(f"+ added new property: '{key}': {default_config[key]}")
                        self.configs[path][key] = default_config[key]
                # for key in self.configs[path]:
                #     if key not in default_config:
                #         if self.verbose:
                #             print(f"- removed property: '{key}': {self.configs[path][key]}")
                #         del self.configs[path][key]
            else:
                if self.verbose:
                    print("config not found, using default:", default_config)
                self.configs[path] = default_config

    def save(self):
        """built-in functions (such as open), do not work in __del__ for whatever reason"""
        try:
            with open(self.path, "w") as f:
                json.dump(self.configs[self.path], f, indent=4)
                if self.verbose:
                    print("writing config:", self.configs[self.path])
        except:
            print("ERROR WHILE WRITING CONFIG???")

    def __getitem__(self, item):
        return self.configs[self.path][item]

    def __setitem__(self, key, value):
        if key in self.__default:
            self.configs[self.path][key] = value

    def __delitem__(self, key):
        del self.configs[self.path][key]

    def __str__(self):
        return str(self.configs[self.path])

    def toggle(self, key):
        if key in self.configs[self.path]:
            val = self.configs[self.path][key]
            if type(val) == bool:
                val = not val
                self.configs[self.path][key] = val
                return val

    def reset_to_defaults(self):
        self.configs[self.path] = self.__default
