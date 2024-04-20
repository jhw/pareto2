"""
Tester dumps to filesystem rather than load tests into memory because of the complexities of handling non- Python assets in memory and getting all the paths right
"""

from pareto2.api.assets import Assets

import importlib.util, os, unittest

class Tester(Assets):

    def __init__(self, item = {}):
        super().__init__(item)

    """
    Refs to __file__ in code bodies have to be rewritten since they won't work in the local filesystem
    """
                 
    def dump_assets(self, root = "tmp"):
        for k, v in self.items():
            dirname = "/".join([root]+k.split("/")[:-1])
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            filename = k.split("/")[-1]
            with open(f"{dirname}/{filename}", 'w') as f:
                f.write(v.replace("__file__", f"\"{root}/{k}\"")) # NB

    def load_module_from_path(self, path):
        spec = importlib.util.spec_from_file_location("module.name", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
                
    def discover_tests(self, root, target_file = "test.py"):
        suite = unittest.TestSuite()
        for root, dirs, files in os.walk(root):
            if target_file in files:
                test_file_path = os.path.join(root, target_file)
                test_module = self.load_module_from_path(test_file_path)
                suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(test_module))
        return suite

    def run_tests(self, root = "tmp"):
        suite = self.discover_tests(root = root)
        if suite.countTestCases() == 0:
            raise RuntimeError("no tests found")
        runner = unittest.TextTestRunner()
        result = runner.run(suite)
        if (result.errors!=[] or
            result.failures!=[]):
            raise RuntimeError("/n".join([error[1] for error in result.errors+result.failures]))

if __name__ == "__main__":
    pass
