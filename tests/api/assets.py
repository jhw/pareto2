from pareto2.api.assets import Assets, file_loader

from moto import mock_s3

import boto3, io, unittest, zipfile

BucketName, Region = "pareto2-assets-test-bucket", "eu-west-1"

PkgRoot = "hello"

@mock_s3
class AssetsTest(unittest.TestCase):

    def setUp(self, bucket_name = BucketName, region = Region):
        self.s3 = boto3.client("s3")
        self.s3.create_bucket(Bucket = bucket_name,
                              CreateBucketConfiguration = {"LocationConstraint": region})
    
    def test_zipped_content(self, pkg_root = PkgRoot):
        assets = Assets(file_loader(pkg_root))
        buf = assets.zipped_content
        zf = zipfile.ZipFile(io.BytesIO(buf))
        filenames = [item.filename for item in zf.infolist()]
        self.assertTrue(f"{pkg_root}/__init__.py" in filenames)
        self.assertTrue(len(filenames) > 1)

    def tearDown(self, bucket_name = BucketName):
        resp = self.s3.list_objects(Bucket = bucket_name)
        if "Contents" in resp:
            for obj in resp["Contents"]:
                self.s3.delete_object(Bucket = bucket_name,
                                      Key = obj["Key"])
        self.s3.delete_bucket(Bucket = bucket_name)
        
if __name__ == "__main__":
    unittest.main()
