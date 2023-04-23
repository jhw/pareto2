from pareto2.scripts.users import fetch_outputs, hungarorise

from botocore.exceptions import ClientError

import boto3, os, re, sys, yaml

if __name__=="__main__":
    try:
        appname=os.environ["APP_NAME"]
        if appname in ["", None]:
            raise RuntimeError("app package not found")
        if len(sys.argv) < 4:
            raise RuntimeError("please enter userpool, email, password")
        userpoolprefix, email, password = sys.argv[1:4]
        if not re.search("^(\\w+\\.)?\\w+\\@\\D+\\.\\D+$", email):
            raise RuntimeError("email is invalid")
        cf=boto3.client("cloudformation")
        stackname=appname
        outputs=fetch_outputs(cf, stackname)
        userpool=hungarorise("%s-user-userpool" % userpoolprefix)
        if userpool not in outputs:
            raise RuntimeError("userpool not found")
        client=hungarorise("%s-user-userpool-web-client" % userpoolprefix)
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

