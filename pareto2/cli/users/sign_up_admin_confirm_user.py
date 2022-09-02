"""
- to be used when you want a ready- made use to test against
"""

from pareto2.cli import *

from pareto2.cli.deploy import fetch_outputs

from botocore.exceptions import ClientError

import boto3, yaml

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 5:
            raise RuntimeError("please enter stage, userpool, email, password")
        stage, userpoolprefix, email, password = sys.argv[1:5]
        if not re.search("^(\\w+\\.)?\\w+\\@\\D+\\.\\D+$", email):
            raise RuntimeError("email is invalid")
        config=load_config()
        cf=boto3.client("cloudformation")
        stackname="%s-%s" % (config["globals"]["AppName"], stage)
        outputs=fetch_outputs(cf, stackname)
        userpool=hungarorise("%s-userpool" % userpoolprefix)
        if userpool not in outputs:
            raise RuntimeError("userpool not found")
        client=hungarorise("%s-userpool-web-client" % userpoolprefix)
        if client not in outputs:
            raise RuntimeError("client not found")
        cognito=boto3.client("cognito-idp")
        resp0=cognito.sign_up(ClientId=outputs[client],
                              Username=email,
                              Password=password)
        print (yaml.safe_dump(resp0,
                              default_flow_style=False))
        resp1=cognito.admin_confirm_sign_up(UserPoolId=outputs[userpool],
                                            Username=email)
        print (yaml.safe_dump(resp1,
                              default_flow_style=False))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))

