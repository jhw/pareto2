from botocore.exceptions import ClientError

import boto3, os, sys

def fetch_layer(L, layername):
    resp=L.list_layers()
    if "Layers" in resp:
        for layer in resp["Layers"]:
            if layer["LayerName"]==layername:
                return layer
    raise RuntimeError("%s not found" % layername)

if __name__=="__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("please enter package name")
        pkgname=sys.argv[1]
        appname=os.environ["APP_NAME"]
        if appname in ["", None]:
            raise RuntimeError("APP_NAME does not exist")
        layername="%s-%s" % (appname, pkgname)
        L=boto3.client("lambda")
        layer=fetch_layer(L, layername)
        print (L.delete_layer_version(LayerName=layer["LayerName"],
                                      VersionNumber=layer["LatestMatchingVersion"]["Version"]))
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
    except ClientError as error:
        print ("Error: %s" % (str(error)))
