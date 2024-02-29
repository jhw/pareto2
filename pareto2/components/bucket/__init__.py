from pareto2.aws.s3 import Bucket as BucketBase

class Bucket(BucketBase):

    def __init__(self, bucket):
        super().__init__(bucket["name"], "bucket")
