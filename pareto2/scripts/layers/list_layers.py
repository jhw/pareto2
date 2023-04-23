from botocore.exceptions import ClientError

import boto3, os

def fetch_layers(L, appname):
    resp, layers = L.list_layers(), []
    if "Layers" in resp:
        for layer in resp["Layers"]:
            if layer["LayerName"].startswith(appname):
                layers.append(layer)
    return layers
    
if __name__=="__main__":
    try:
        appname=os.environ["APP_NAME"]
        if appname in ["", None]:
            raise RuntimeError("APP_NAME does not exist")
        L=boto3.client("lambda")
        layers=fetch_layers(L, appname)
        for layer in layers:
            print ("%s :: %s" % (layer["LayerName"],
                                 layer["LatestMatchingVersion"]["LayerVersionArn"]))
    except ClientError as error:
        print ("Error: %s" % str(error))
    except RuntimeError as error:
        print ("Error: %s" % str(error))

