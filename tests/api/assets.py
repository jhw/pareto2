from pareto2.api.assets import Assets, file_loader

from tests.api import ApiTestBase, BucketName

from moto import mock_s3

import io, unittest, zipfile

PkgRoot = "hello"

@mock_s3
class AssetsTest(ApiTestBase):

    def setUp(self):
        super().setUp()
    
    def test_file_to_zip(self,
                         pkg_root = PkgRoot,
                         bucket_name = BucketName,
                         key = "assets.zip"):
        assets = Assets(file_loader(pkg_root))
        assets.dump_s3(s3 = self.s3,
                       bucket_name = bucket_name,
                       key = key)
        zf=zipfile.ZipFile(io.BytesIO(self.s3.get_object(Bucket=bucket_name,
                                                         Key=key)["Body"].read()))
        filenames = [item.filename for item in zf.infolist()]
        self.assertTrue(f"{pkg_root}/__init__.py" in filenames)
        self.assertTrue(len(filenames) > 1)
    
    def tearDown(self):
        super().tearDown()
        
if __name__ == "__main__":
    unittest.main()
