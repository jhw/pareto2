from pareto2.cli import hungarorise, fetch_outputs

from pareto2.cli.deploy import *

from botocore.exceptions import ClientError

import boto3

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 3:
            raise RuntimeError("please enter stage, apiname")
        stagename, apiname = sys.argv[1:3]
        from pareto2.cli import load_config
        config=load_config()
        cf=boto3.client("cloudformation")
        stackname="%s-%s" % (config["AppName"],
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
