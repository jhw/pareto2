from pareto2.api import file_loader
from pareto2.api.tester import Tester

import unittest

PkgRoot = "hello"

class ApiTesterTest(unittest.TestCase):

    def test_tester(self,
                    pkg_root = PkgRoot):
        tester = Tester({k:v for k, v in file_loader(pkg_root)})
        tester.dump_assets()
        tester.run_tests()

if __name__ == "__main__":
    unittest.main()
        
