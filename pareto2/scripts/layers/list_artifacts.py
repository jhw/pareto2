import boto3

def list_bucket(s3, bucketname, prefix="layer-"):
    paginator=s3.get_paginator("list_objects_v2")
    pages=paginator.paginate(Bucket=bucketname,
                             Prefix=prefix)
    for struct in pages:
        if "Contents" in struct:
            for obj in struct["Contents"]:
                print ("%i\t%s" % (obj["Size"], obj["Key"]))

if __name__=="__main__":
    try:
        from pareto2.scripts.helpers import load_config
        config=load_config()
        s3=boto3.client("s3")
        list_bucket(s3, config["ArtifactsBucket"])
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
