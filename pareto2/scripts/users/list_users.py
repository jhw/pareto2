from pareto2.scripts.users import *

import boto3, yaml

from botocore.exceptions import ClientError

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stage")
        stage=sys.argv[1]
        config=load_config()
        cf=boto3.client("cloudformation")
        stackname="%s-%s" % (config["AppName"], stage)
        outputs=load_outputs(cf, stackname)
        if UserPool not in outputs:
            raise RuntimeError("user pool not found")
        cognito=boto3.client("cognito-idp")
        resp=cognito.list_users(UserPoolId=outputs[UserPool])
        print (yaml.safe_dump(resp,
                              default_flow_style=False))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))

