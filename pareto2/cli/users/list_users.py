from pareto2.cli import *

from pareto2.cli.deploy import fetch_outputs

from botocore.exceptions import ClientError

import boto3, yaml

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 3:
            raise RuntimeError("please enter stage, userpool")
        stage, userpoolprefix = sys.argv[1:3]
        config=load_config()
        cf=boto3.client("cloudformation")
        stackname="%s-%s" % (config["AppName"], stage)
        outputs=fetch_outputs(cf, stackname)
        userpool=hungarorise("%s-userpool" % userpoolprefix)
        if userpool not in outputs:
            raise RuntimeError("userpool not found")
        cognito=boto3.client("cognito-idp")
        resp=cognito.list_users(UserPoolId=outputs[userpool])
        print (yaml.safe_dump(resp,
                              default_flow_style=False))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))

