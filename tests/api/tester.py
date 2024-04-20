from pareto2.api import file_loader
from pareto2.api.tester import Tester

from tests.api import ApiTestBase, BucketName

from moto import mock_s3

import unittest

PkgRoot = "hello"

@mock_s3
class ApiTesterTest(ApiTestBase):

    def setUp(self):
        super().setUp()
    
    def test_tester(self,
                    pkg_root = PkgRoot):
        tester = Tester({k:v for k, v in file_loader(pkg_root)})
        self.assertEqual(2, 2)

    def tearDown(self):
        super().tearDown()
        
if __name__ == "__main__":
    unittest.main()
        
