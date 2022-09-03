from pareto2.cli.deploy import fetch_outputs

from pareto2.core.components import hungarorise

from pareto2.core.dsl import Config

from botocore.exceptions import ClientError

import boto3, re, sys, yaml

if __name__=="__main__":
    try:
        if len(sys.argv) < 5:
            raise RuntimeError("please enter stage, userpool, email, password")
        stage, userpoolprefix, email, password = sys.argv[1:5]
        if not re.search("^(\\w+\\.)?\\w+\\@\\D+\\.\\D+$", email):
            raise RuntimeError("email is invalid")
        config=Config.initialise()
        cf=boto3.client("cloudformation")
        stackname="%s-%s" % (config["globals"]["app-name"], stage)
        outputs=fetch_outputs(cf, stackname)
        userpool=hungarorise("%s-userpool" % userpoolprefix)
        if userpool not in outputs:
            raise RuntimeError("userpool not found")
        client=hungarorise("%s-userpool-admin-client" % userpoolprefix)
        if client not in outputs:
            raise RuntimeError("client not found")
        cognito=boto3.client("cognito-idp")
        params={"USERNAME": email,
                "PASSWORD": password}
        resp=cognito.admin_initiate_auth(UserPoolId=outputs[userpool],
                                         ClientId=outputs[client],
                                         AuthFlow='ADMIN_NO_SRP_AUTH',
                                         AuthParameters=params)
        print (yaml.safe_dump(resp,
                              default_flow_style=False))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))

