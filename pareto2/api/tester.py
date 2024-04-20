from pareto2.api.assets import Assets

import importlib.util, os, unittest

class Tester(Assets):


    def __init__(self, item = {}):
        super().__init__(item)

    """
    Refs to __file__ in code bodies have to be rewritten since they won't work in the local filesystem
    """
                 
    def dump(self, root = "tmp"):
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
                
    def discover_tests(self, root = "tmp", target_file = "test.py"):
        suite = unittest.TestSuite()
        for root, dirs, files in os.walk(root):
            if target_file in files:
                test_file_path = os.path.join(root, target_file)
                test_module = self.load_module_from_path(test_file_path)
                suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(test_module))
        return suite
                
if __name__ == "__main__":
    pass
