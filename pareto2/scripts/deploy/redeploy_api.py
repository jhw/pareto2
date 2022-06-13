from botocore.exceptions import ClientError

import boto3

def load_outputs(cf, stackname):
    outputs={}
    for stack in cf.describe_stacks()["Stacks"]:
        if (stack["StackName"].startswith(stackname) and
            "Outputs" in stack):
            for output in stack["Outputs"]:
                outputs[output["OutputKey"]]=output["OutputValue"]
    return outputs

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stage")
        stagename=sys.argv[1]
        from scripts.helpers import load_config
        config=load_config()
        cf=boto3.client("cloudformation")
        stackname="%s-%s" % (config["AppName"],
                             stagename)
        outputs=load_outputs(cf, stackname)
        apigw=boto3.client("apigateway")
        print (apigw.create_deployment(restApiId=outputs["ApiRestApi"],
                                       stageName=outputs["ApiStage"]))
    except ClientError as error:
        print (error)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
