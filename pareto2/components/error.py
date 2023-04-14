from pareto2.components import hungarorise as H
from pareto2.components import resource

FunctionCode="""
from urllib import request

import boto3, json, os

# https://colorswall.com/palette/3

Levels={"info":  "#5bc0de",
        "warning": "#f0ad4e",
        "error": "#d9534f"}

def post_webhook(struct, url):
    req=request.Request(url, method="POST")
    req.add_header("Content-Type", "application/json")
    data=json.dumps(struct).encode()
    resp=request.urlopen(req, data=data)
    return resp.read()

def handler(event, context=None,
            levels=Levels,
            webhookurl=os.environ["SLACK_ERROR_WEBHOOK"]):
    text=json.dumps(event)
    color=levels["error"]
    struct={"attachments": [{"text": text,
                             "color": color}]}
    post_webhook(struct, webhookurl)
"""

@resource            
def init_function(error,
                  code=FunctionCode):
    resourcename=H("%s-function" % error["name"])
    rolename=H("%s-function-role" % error["name"])
    code={"ZipFile": code}
    runtime={"Fn::Sub": "python${%s}" % H("runtime-version")}
    """
    memorysize=H("memory-size-%s" % error["streaming"]["size"])
    timeout=H("timeout-%s" % error["streaming"]["timeout"])
    """
    variables={}
    props={"Role": {"Fn::GetAtt": [rolename, "Arn"]},
           "MemorySize": {"Ref": memorysize},
           "Timeout": {"Ref": timeout},
           "Code": code,
           "Handler": "index.handler",
           "Runtime": runtime,
           "Environment": {"Variables": variables}}
    return (resourcename, 
            "AWS::Lambda::Function",
            props)

@resource
def init_function_role(error,
                       permissions=["logs:CreateLogGroup",
                                    "logs:CreateLogStream",
                                    "logs:PutLogEvents"]):
    def group_permissions(permissions):
        groups={}
        for permission in permissions:
            prefix=permission.split(":")[0]
            groups.setdefault(prefix, [])
            groups[prefix].append(permission)
        return [sorted(group)
                for group in list(groups.values())]
    resourcename=H("%s-function-role" % error["name"])
    assumerolepolicydoc={"Version": "2012-10-17",
                         "Statement": [{"Action": "sts:AssumeRole",
                                        "Effect": "Allow",
                                        "Principal": {"Service": "lambda.amazonaws.com"}}]}
    policydoc={"Version": "2012-10-17",
               "Statement": [{"Action" : group,
                              "Effect": "Allow",
                              "Resource": "*"}
                             for group in group_permissions(permissions)]}
    policyname={"Fn::Sub": "%s-function-role-policy-${AWS::StackName}" % error["name"]}
    policies=[{"PolicyDocument": policydoc,
               "PolicyName": policyname}]
    props={"AssumeRolePolicyDocument": assumerolepolicydoc,
           "Policies": policies}
    return (resourcename,
            "AWS::IAM::Role",
            props)

def render_resources(error):
    resources=[]
    for fn in [init_function,
               init_function_role]:
        resource=fn(error)
        resources.append(resource)
    return dict(resources)

def render_outputs(error):
    return {}
                               
if __name__=="__main__":
    pass
