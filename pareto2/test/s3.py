import boto3, yaml

TestBucket=yaml.safe_load("""
name: test-bucket
""")

class Pareto2S3TestMixin:

    def setup_s3(self, buckets=[TestBucket]):
        def create_bucket(s3, bucket):
            config={'LocationConstraint': 'EU'}
            s3.create_bucket(Bucket=bucket["name"],
                             CreateBucketConfiguration=config)
        self.s3=boto3.client("s3")
        for bucket in buckets:
            create_bucket(self.s3, bucket)

    def teardown_s3(self, buckets=[TestBucket]):
        def empty_bucket(s3, bucket):            
            struct=s3.list_objects(Bucket=bucket["name"])
            if "Contents" in struct:
                for obj in struct["Contents"]:
                    s3.delete_object(Bucket=bucket["name"],
                                     Key=obj["Key"])
        def delete_bucket(s3, bucket):
            s3.delete_bucket(Bucket=bucket["name"])
        for bucket in buckets:
            empty_bucket(self.s3, bucket)
            delete_bucket(self.s3, bucket)

if __name__=="___main__":
    pass
