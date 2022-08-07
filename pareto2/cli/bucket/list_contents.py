import boto3

def list_contents(s3, bucketname, prefix):
    paginator=s3.get_paginator("list_objects_v2")
    kwargs={"Bucket": bucketname}
    if prefix:
        kwargs["Prefix"]=prefix
    pages=paginator.paginate(**kwargs)
    for struct in pages:
        if "Contents" in struct:
            for obj in struct["Contents"]:
                print (obj["Key"])
    
if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter bucket name, prefix?")
        bucketname=sys.argv[1]
        prefix=sys.argv[2] if len(sys.argv) > 2 else None            
        s3=boto3.client("s3")
        list_contents(s3, bucketname, prefix)
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
