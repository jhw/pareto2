"""
- to be used when you want to initialise a user, but the user themselves has to complete the auth flow
- in particular user will need to change password, as user state after admin_create_user is FORCE_CHANGE_PASSWORD
- this is reasonably easy with Amplify auth on JS side, but much harder with noto3 on Python side (so don't try)
- auth routine could be expanded into full onboarding routine including podcast channel details, image upload etc
"""

from scripts.users import *

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
        resp=cognito.admin_create_user(UserPoolId=outputs[UserPool],
                                       Username=email,
                                       DesiredDeliveryMediums=["EMAIL"])
        print (yaml.safe_dump(resp,
                              default_flow_style=False))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))

