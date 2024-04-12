import boto3, unittest

BucketName, Region = "pareto2-assets-test-bucket", "eu-west-1"

class ApiTestBase(unittest.TestCase):

    def setUp(self, bucket_name = BucketName, region = Region):
        self.s3 = boto3.client("s3")
        self.s3.create_bucket(Bucket = bucket_name,
                              CreateBucketConfiguration = {"LocationConstraint": region})
    
    def tearDown(self, bucket_name = BucketName):
        resp = self.s3.list_objects(Bucket = bucket_name)
        if "Contents" in resp:
            for obj in resp["Contents"]:
                self.s3.delete_object(Bucket = bucket_name,
                                      Key = obj["Key"])
        self.s3.delete_bucket(Bucket = bucket_name)
        
if __name__ == "__main__":
    unittest.main()
