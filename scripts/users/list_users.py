from botocore.exceptions import ClientError

import boto3, json, os, re, sys

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
        if len(sys.argv) < 3:
            raise RuntimeError("please enter stackname, namespace")
        stackname, namespace = sys.argv[1:3]
        cf=boto3.client("cloudformation")
        outputs=fetch_outputs(cf, stackname)
        userpoolkey=hungarorise(f"{namespace}-user-pool")
        if userpoolkey not in outputs:
            raise RuntimeError("userpool not found")
        userpool=outputs[userpoolkey]
        cognito=boto3.client("cognito-idp")
        resp=cognito.list_users(UserPoolId=userpool)
        print (json.dumps(resp, indent=2))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))

