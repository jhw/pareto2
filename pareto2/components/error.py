from pareto2.components import hungarorise as H
from pareto2.components import uppercase as U
from pareto2.components import resource

SlackFunctionCode="""
from urllib import request

import base64, gzip, json, os

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
    struct=json.loads(gzip.decompress(base64.b64decode(event["awslogs"]["data"])))
    text=json.dumps(struct)
    color=levels["error"]
    struct={"attachments": [{"text": text,
                             "color": color}]}
    post_webhook(struct, webhookurl)
"""

@resource            
def init_slack_function(error,
                        envvars=["slack-error-webhook"],
                        code=SlackFunctionCode):
    resourcename=H("%s-slack-function" % error["name"])
    rolename=H("%s-slack-function-role" % error["name"])
    code={"ZipFile": code}
    runtime={"Fn::Sub": "python${%s}" % H("runtime-version")}
    memorysize=H("memory-size-%s" % error["function"]["size"])
    timeout=H("timeout-%s" % error["function"]["timeout"])
    variables={U(k): {"Ref": H(k)}
               for k in envvars}
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
def init_slack_function_role(error,
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
    resourcename=H("%s-slack-function-role" % error["name"])
    assumerolepolicydoc={"Version": "2012-10-17",
                         "Statement": [{"Action": "sts:AssumeRole",
                                        "Effect": "Allow",
                                        "Principal": {"Service": "lambda.amazonaws.com"}}]}
    policydoc={"Version": "2012-10-17",
               "Statement": [{"Action" : group,
                              "Effect": "Allow",
                              "Resource": "*"}
                             for group in group_permissions(permissions)]}
    policyname={"Fn::Sub": "%s-slack-function-role-policy-${AWS::StackName}" % error["name"]}
    policies=[{"PolicyDocument": policydoc,
               "PolicyName": policyname}]
    props={"AssumeRolePolicyDocument": assumerolepolicydoc,
           "Policies": policies}
    return (resourcename,
            "AWS::IAM::Role",
            props)

@resource
def init_slack_logs_permission(error):
    resourcename=H("%s-slack-logs-permission" % error["name"])
    funcname={"Ref": H("%s-slack-function" % error["name"])}
    props={"Action": "lambda:InvokeFunction",
           "Principal": "logs.amazonaws.com",
           "FunctionName": funcname}
    return (resourcename,
            "AWS::Lambda::Permission",
            props)

def render_resources(error):
    resources=[]
    for fn in [init_slack_function,
               init_slack_function_role,
               init_slack_logs_permission]:
        resource=fn(error)
        resources.append(resource)
    return dict(resources)

def render_outputs(error):
    return {}

if __name__=="__main__":
    pass