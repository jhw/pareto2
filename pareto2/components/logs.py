from pareto2.components import hungarorise as H
from pareto2.components import uppercase as U
from pareto2.components import resource

from pareto2.components.common.iam import policy_document, assume_role_policy_document

SlackFunctionCode="""import base64, gzip, json, os, urllib.request

# https://colorswall.com/palette/3

Levels={"info":  "#5bc0de",
        "warning": "#f0ad4e",
        "error": "#d9534f"}

def post_webhook(struct, url):
    req=urllib.request.Request(url, method="POST")
    req.add_header("Content-Type", "application/json")
    data=json.dumps(struct).encode()
    return urllib.request.urlopen(req, data=data).read()

def handler(event, context=None,
            colour=Levels[os.environ["SLACK_LOGGING_LEVEL"]],
            webhookurl=os.environ["SLACK_WEBHOOK_URL"]):
    struct=json.loads(gzip.decompress(base64.b64decode(event["awslogs"]["data"])))
    text=json.dumps(struct)
    struct={"attachments": [{"text": text,
                             "color": colour}]}
    post_webhook(struct, webhookurl)"""

@resource            
def init_function(logs,
                  code=SlackFunctionCode):
    resourcename=H("%s-logs-function" % logs["name"])
    rolename=H("%s-logs-function-role" % logs["name"])
    code={"ZipFile": code}
    runtime={"Fn::Sub": "python${%s}" % H("runtime-version")}
    memorysize=H("memory-size-%s" % logs["function"]["size"])
    timeout=H("timeout-%s" % logs["function"]["timeout"])
    variables={U("slack-webhook-url"): {"Ref": H("slack-webhook-url")},
               U("slack-logging-level"): logs["level"]}
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
def init_function_role(logs,
                       permissions=["logs:CreateLogGroup",
                                    "logs:CreateLogStream",
                                    "logs:PutLogEvents"]):
    resourcename=H("%s-logs-function-role" % logs["name"])
    policyname={"Fn::Sub": "%s-logs-function-role-policy-${AWS::StackName}" % logs["name"]}
    policydoc=policy_document(permissions)
    policies=[{"PolicyDocument": policydoc,
               "PolicyName": policyname}]
    props={"AssumeRolePolicyDocument": assume_role_policy_document(),
           "Policies": policies}
    return (resourcename,
            "AWS::IAM::Role",
            props)

@resource
def init_permission(logs):
    resourcename=H("%s-logs-permission" % logs["name"])
    funcname={"Ref": H("%s-logs-function" % logs["name"])}
    props={"Action": "lambda:InvokeFunction",
           "Principal": "logs.amazonaws.com",
           "FunctionName": funcname}
    return (resourcename,
            "AWS::Lambda::Permission",
            props)

def render_resources(logs):
    resources=[]
    for fn in [init_function,
               init_function_role,
               init_permission]:
        resource=fn(logs)
        resources.append(resource)
    return dict(resources)

def render_outputs(logs):
    return {}

if __name__=="__main__":
    pass
