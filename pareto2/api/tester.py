"""
Tester dumps to filesystem rather than load tests into memory because of the complexities of handling non- Python assets in memory and getting all the paths right
"""

from pareto2.api.assets import Assets

import importlib.util
import os
import traceback
import unittest

"""
/tmp guaranteed to exist on both Lambda and Unix systems in general

On OSX it is generally a symlink to /private/tmp
"""

Root = "/tmp"

class Tester(Assets):

    def __init__(self, root = Root, item = {}):
        super().__init__(item)
        self.root = root

    """
    Refs to __file__ in code bodies have to be rewritten since they won't work in the local filesystem
    """

    def dump_assets(self):
        for k, v in self.items():
            dirname = "/".join([self.root]+k.split("/")[:-1])
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            filename = k.split("/")[-1]
            with open(f"{dirname}/{filename}", 'w') as f:
                f.write(v.replace("__file__", f"\"{self.root}/{k}\"")) # NB

    """
    try/catch block employed because a target app could include garbage code which, when imported, could bring down a pipeline unless correctly handled
    """
                
    def load_module_from_path(self, path):
        try:
            spec = importlib.util.spec_from_file_location("module.name", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except:
            tb = traceback.format_exc()
            raise RuntimeError(f"error loading {path}: {tb}")

    """
    cache because historically have got into some recursive loops when tests call handlers which run tests
    """

    def discover_tests(self,
                       target_file = "test.py",
                       cache = set()):
        suite = unittest.TestSuite()
        for root, dirs, files in os.walk(self.root):
            if target_file in files:
                test_file_path = os.path.join(root, target_file)
                if test_file_path not in cache:
                    test_module = self.load_module_from_path(test_file_path)
                    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(test_module))
                    cache.add(test_file_path)
        return suite

    def run_tests(self):
        suite = self.discover_tests()
        if suite.countTestCases() == 0:
            raise RuntimeError("no tests found")
        runner = unittest.TextTestRunner()
        result = runner.run(suite)
        if (result.errors!=[] or
            result.failures!=[]):
            raise RuntimeError("/n".join([error[1] for error in result.errors+result.failures]))

if __name__ == "__main__":
    pass
