from pareto2.core.dsl import Config

from botocore.exceptions import ClientError

import boto3, sys

if __name__=="__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("please enter object key")
        key=sys.argv[1]
        config=Config.initialise()
        bucketname=config["globals"]["ArtifactsBucket"]
        s3=boto3.client("s3")        
        resp=s3.get_object(Bucket=bucketname,
                           Key=key)
        with open("tmp/%s" % key, 'wb') as f:
            f.write(resp["Body"].read())
    except RuntimeError as error:
        print ("Error: %s" % (str(error)))
    except ClientError as error:
        print ("Error: %s" % (str(error)))
