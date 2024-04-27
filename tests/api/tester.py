from pareto2.api import file_loader
from pareto2.api.tester import Tester

import os, unittest

class ApiTesterTest(unittest.TestCase):

    def test_tester(self,
                    pkg_root = "hello"):
        if os.path.exists("/tmp"):
            os.system("rm -rf /tmp/*")
        tester = Tester(item = {k:v for k, v in file_loader(pkg_root)})
        tester.dump_assets()
        tester.run_tests()

if __name__ == "__main__":
    unittest.main()
        
