from pareto2.cli.users import *

import boto3, yaml

from botocore.exceptions import ClientError

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 3:
            raise RuntimeError("please enter stage, email")
        stage, email = sys.argv[1:3]
        if not re.search("^(\\w+\\.)?\\w+\\@\\D+\\.\\D+$", email):
            raise RuntimeError("email is invalid")
        config=load_config()
        cf=boto3.client("cloudformation")
        stackname="%s-%s" % (config["AppName"], stage)
        outputs=load_outputs(cf, stackname)
        if UserPool not in outputs:
            raise RuntimeError("user pool not found")
        cognito=boto3.client("cognito-idp")
        resp=cognito.admin_delete_user(UserPoolId=outputs[UserPool],
                                       Username=email)
        print (yaml.safe_dump(resp,
                              default_flow_style=False))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))

