from pareto2.api.assets import Assets, file_loader, s3_zip_loader

from tests.api import ApiTestBase, BucketName

from moto import mock_s3

import io, unittest, zipfile

PkgRoot = "hello"

@mock_s3
class ApiAssetsTest(ApiTestBase):

    def setUp(self):
        super().setUp()
    
    def test_round_trip(self,
                        pkg_root = PkgRoot,
                        bucket_name = BucketName,
                        key = "assets.zip"):
        assets = Assets({k:v for k, v in file_loader(pkg_root)})
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
