from pareto2.cli.deploy import *

from pareto2.core.dsl import Config

from pareto2.core.components import hungarorise

from botocore.exceptions import ClientError

import boto3, sys

if __name__=="__main__":
    try:
        if len(sys.argv) < 3:
            raise RuntimeError("please enter stage, apiname")
        stagename, apiname = sys.argv[1:3]
        config=Config.initialise()
        cf=boto3.client("cloudformation")
        stackname="%s-%s" % (config["globals"]["app-name"],
                             stagename)
        outputs=fetch_outputs(cf, stackname)
        restapiname=hungarorise("%s-api-rest-api" % apiname)
        if restapiname not in outputs:
            raise RuntimeError("%s not found" % restapiname)
        stagename=hungarorise("%s-api-stage" % apiname)
        if stagename not in outputs:
            raise RuntimeError("%s not found" % stagename)
        apigw=boto3.client("apigateway")
        print (apigw.create_deployment(restApiId=outputs[restapiname],
                                       stageName=outputs[stagename]))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))
