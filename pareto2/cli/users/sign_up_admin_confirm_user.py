"""
- to be used when you want a ready- made use to test against
"""

from pareto2.cli.users import *

import boto3, yaml

from botocore.exceptions import ClientError

WebClient="UsersWebClient"

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 4:
            raise RuntimeError("please enter stage, email, password")
        stage, email, password = sys.argv[1:4]
        if not re.search("^(\\w+\\.)?\\w+\\@\\D+\\.\\D+$", email):
            raise RuntimeError("email is invalid")
        config=load_config()
        cf=boto3.client("cloudformation")
        stackname="%s-%s" % (config["AppName"], stage)
        outputs=load_outputs(cf, stackname)
        if UserPool not in outputs:
            raise RuntimeError("user pool not found")
        if WebClient not in outputs:
            raise RuntimeError("web client not found")
        cognito=boto3.client("cognito-idp")
        resp0=cognito.sign_up(ClientId=outputs[WebClient],
                              Username=email,
                              Password=password)
        print (yaml.safe_dump(resp0,
                              default_flow_style=False))
        resp1=cognito.admin_confirm_sign_up(UserPoolId=outputs[UserPool],
                                            Username=email)
        print (yaml.safe_dump(resp1,
                              default_flow_style=False))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))

