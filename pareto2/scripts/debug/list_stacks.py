from botocore.exceptions import ClientError

import boto3, os

def format_value(value, n = 32):
    text = str(value)
    return text[:n] if len(text) > n else text+"".join([" " for i in range(n-len(text))])

if __name__ == "__main__":
    try:
        cf = boto3.client("cloudformation")
        for stack in reversed(sorted(cf.describe_stacks()["Stacks"],
                                     key = lambda x: x["CreationTime"])):
            print ("%s %s %s" % (format_value(stack["StackName"]),
                                 format_value(stack["StackStatus"]),
                                 format_value(stack["CreationTime"])))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))
        
