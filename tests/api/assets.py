from pareto2.api import file_loader, s3_zip_loader
from pareto2.api.assets import Assets

from tests.api import ApiTestBase, BucketName

from moto import mock_s3

import io, unittest, zipfile

@mock_s3
class ApiAssetsTest(ApiTestBase):

    def setUp(self):
        super().setUp()
    
    def test_round_trip(self,
                        app_name = "hello",
                        pkg_root = "hello",
                        bucket_name = BucketName,
                        key = "assets.zip"):
        path_rewriter = lambda x: "/".join(x.split("/")[1:])
        assets = Assets({k:v for k, v in file_loader(f"{app_name}/{pkg_root}",
                                                     path_rewriter = path_rewriter)})
        assets.dump_s3(s3 = self.s3,
                       bucket_name = bucket_name,
                       key = key)
        filenames = [key_ for key_, _ in s3_zip_loader(s3 = self.s3,
                                                       bucket_name = bucket_name,
                                                       key = key)]
        self.assertTrue(f"{pkg_root}/__init__.py" in filenames)
        self.assertTrue(len(filenames) > 1)

    def tearDown(self):
        super().tearDown()
        
if __name__ == "__main__":
    unittest.main()
