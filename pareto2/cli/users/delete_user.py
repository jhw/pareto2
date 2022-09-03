from pareto2.cli.deploy import fetch_outputs

from pareto2.core.components import hungarorise

from pareto2.core.dsl import Config

from botocore.exceptions import ClientError

import boto3, sys, yaml

if __name__=="__main__":
    try:
        if len(sys.argv) < 4:
            raise RuntimeError("please enter stage, userpool, email")
        stage, userpoolprefix, email = sys.argv[1:4]
        if not re.search("^(\\w+\\.)?\\w+\\@\\D+\\.\\D+$", email):
            raise RuntimeError("email is invalid")
        config=Config.initialise()
        cf=boto3.client("cloudformation")
        stackname="%s-%s" % (config["globals"]["AppName"], stage)
        outputs=fetch_outputs(cf, stackname)
        userpool=hungarorise("%s-userpool" % userpoolprefix)
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

