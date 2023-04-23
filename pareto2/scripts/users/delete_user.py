from pareto2.scripts.users import fetch_outputs, hungarorise

from botocore.exceptions import ClientError

import boto3, os, re, sys, yaml

if __name__=="__main__":
    try:
        appname=os.environ["APP_NAME"]
        if appname in ["", None]:
            raise RuntimeError("app package not found")
        if len(sys.argv) < 3:
            raise RuntimeError("please enter userpool, email")
        userpoolprefix, email = sys.argv[1:3]
        if not re.search("^(\\w+\\.)?\\w+\\@\\D+\\.\\D+$", email):
            raise RuntimeError("email is invalid")
        cf=boto3.client("cloudformation")
        stackname=appname
        outputs=fetch_outputs(cf, stackname)
        userpool=hungarorise("%s-user-userpool" % userpoolprefix)
        if userpool not in outputs:
            raise RuntimeError("userpool not found")
        cognito=boto3.client("cognito-idp")
        resp=cognito.admin_delete_user(UserPoolId=outputs[userpool],
                                       Username=email)
        print (yaml.safe_dump(resp,
                              default_flow_style=False))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))

