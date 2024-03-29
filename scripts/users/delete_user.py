from botocore.exceptions import ClientError

import boto3, os, re, sys, yaml

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
        props=dict([tuple(row.split("="))
                    for row in open("app.props").read().split("\n")
                    if row!=''])
        stackname=props["AppName"]
        if len(sys.argv) < 2:
            raise RuntimeError("please enter email")
        email=sys.argv[1]
        cf=boto3.client("cloudformation")
        outputs=fetch_outputs(cf, stackname)
        userpoolkey=hungarorise("app-user-pool")
        if userpoolkey not in outputs:
            raise RuntimeError("userpool not found")
        userpool=outputs[userpoolkey]
        cognito=boto3.client("cognito-idp")
        resp=cognito.admin_delete_user(UserPoolId=userpool,
                                       Username=email)
        print (yaml.safe_dump(resp,
                              default_flow_style=False))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))

