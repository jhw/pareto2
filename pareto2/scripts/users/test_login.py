from scripts.users import *

import boto3, re, yaml

from botocore.exceptions import ClientError

AdminClient="UsersAdminClient"

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
        if AdminClient not in outputs:
            raise RuntimeError("admin client not found")
        cognito=boto3.client("cognito-idp")
        params={"USERNAME": email,
                "PASSWORD": password}
        resp=cognito.admin_initiate_auth(UserPoolId=outputs[UserPool],
                                         ClientId=outputs[AdminClient],
                                         AuthFlow='ADMIN_NO_SRP_AUTH',
                                         AuthParameters=params)
        print (yaml.safe_dump(resp,
                              default_flow_style=False))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))

