from botocore.exceptions import ClientError

import boto3, os, sys

def fetch_names(L, appname):
    resp, names = L.list_layers(), []
    if "Layers" in resp:
        for layer in resp["Layers"]:
            if layer["LayerName"].startswith(appname):
                names.append(layer["LayerName"])
    return names

def fetch_keys(s3, bucketname, prefix="layer"):
    paginator=s3.get_paginator("list_objects_v2")
    kwargs={"Bucket": bucketname,
            "Prefix": prefix}
    pages=paginator.paginate(**kwargs)
    keys=[]
    for struct in pages:
        if "Contents" in struct:
            for obj in struct["Contents"]:
                keys.append(obj["Key"])
    return keys
    
if __name__=="__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("please enter package name")
        pkgname=sys.argv[1]
        appname=os.environ["APP_NAME"]
        if appname in ["", None]:
            raise RuntimeError("APP_NAME does not exist")
        bucketname=os.environ["ARTIFACTS_BUCKET"]
        if bucketname in ["", None]:
            raise RuntimeError("ARTIFACTS_BUCKET does not exist")
        s3, L = (boto3.client("s3"),
                 boto3.client("lambda"))
        layernames=fetch_names(L, appname)
        layername="%s-%s" % (appname, pkgname)
        if layername in layernames:
            raise RuntimeError("%s already exists" % layername)
        layerkeys=fetch_keys(s3, bucketname)
        layerkey="layer-%s.zip" % pkgname
        if layerkey not in layerkeys:
            raise RuntimeError("%s does not exist" % layerkey)
        print (L.publish_layer_version(LayerName=layername,
                                       Content={"S3Bucket": bucketname,
                                                "S3Key": layerkey}))
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
    except ClientError as error:
        print ("Error: %s" % (str(error)))
