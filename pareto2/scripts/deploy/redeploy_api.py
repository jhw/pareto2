from botocore.exceptions import ClientError

import boto3, os, re, sys

def hungarorise(text):
    return "".join([tok.capitalize()
                    for tok in re.split("\\-|\\_", text)])

def fetch_outputs(cf, stackname):
    outputs={}
    for stack in cf.describe_stacks()["Stacks"]:
        if (stack["StackName"].startswith(stackname) and
            "Outputs" in stack):
            for output in stack["Outputs"]:
                outputs[output["OutputKey"]]=output["OutputValue"]
    return outputs

if __name__=="__main__":
    try:
        appname=os.environ["APP_NAME"]
        if appname in ["", None]:
            raise RuntimeError("APP_NAME does not exist")
        if len(sys.argv) < 2:
            raise RuntimeError("please enter apiname")
        apiname=sys.argv[1]
        cf=boto3.client("cloudformation")
        outputs=fetch_outputs(cf, stackname=appname)
        restapiname=hungarorise("%s-rest-api" % apiname)
        if restapiname not in outputs:
            raise RuntimeError("%s not found" % restapiname)
        stagename=hungarorise("%s-stage" % apiname)
        if stagename not in outputs:
            raise RuntimeError("%s not found" % stagename)
        apigw=boto3.client("apigateway")
        print (apigw.create_deployment(restApiId=outputs[restapiname],
                                       stageName=outputs[stagename]))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))
