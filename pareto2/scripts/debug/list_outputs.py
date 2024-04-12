from botocore.exceptions import ClientError

import boto3, os

def format_value(value, n=32):
    text=str(value)
    return text[:n] if len(text) > n else text+"".join([" " for i in range(n-len(text))])

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
        stackname=os.environ["APP_NAME"]
        if stackname in ["", None]:
            raise RuntimeError("APP_NAME not found")
        cf=boto3.client("cloudformation")
        outputs=fetch_outputs(cf, stackname)
        for k in sorted(outputs.keys()):
            print ("%s\t%s" % (format_value(k),
                               outputs[k]))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))
        
