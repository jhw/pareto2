import boto3

Region="eu-west-1"

def create_bucket(s3, bucketname, region=Region):
    location={"LocationConstraint": region}
    print (s3.create_bucket(Bucket=bucketname,
                            CreateBucketConfiguration=location))
    
if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter bucket name")
        bucketname=sys.argv[1]
        s3=boto3.client("s3")
        create_bucket(s3, bucketname)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
