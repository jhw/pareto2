from pareto2.components import hungarorise as H
from pareto2.components import uppercase as U
from pareto2.components import resource

from pareto2.components.common.iam import policy_document, assume_role_policy_document

SlackFunctionCode="""import json, os, urllib.request

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
            colour=Levels["warning"],
            webhookurl=os.environ["SLACK_WEBHOOK_URL"]):
    body={"event": event, "context": context}
    struct={"attachments": [{"text": str(body),
                             "color": colour}]}
    post_webhook(struct, webhookurl)"""

SlackSize, SlackTimeout = "default", "default"

@resource            
def init_dlq_function(queue,
                      size=SlackSize,
                      timeout=SlackTimeout,
                      envvars=["slack-webhook-url"],
                      code=SlackFunctionCode):
    resourcename=H("%s-queue-dlq-function" % queue["name"])
    rolename=H("%s-queue-dlq-function-role" % queue["name"])
    code={"ZipFile": code}
    runtime={"Fn::Sub": "python${%s}" % H("runtime-version")}
    memorysize=H("memory-size-%s" % size)
    timeout=H("timeout-%s" % timeout)
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
def init_dlq_function_role(queue,
                           permissions=["logs:CreateLogGroup",
                                        "logs:CreateLogStream",
                                        "logs:PutLogEvents",
                                        "sqs:DeleteMessage",
                                        "sqs:GetQueueAttributes",
                                        "sqs:ReceiveMessage"]):
    resourcename=H("%s-queue-dlq-function-role" % queue["name"])
    policyname={"Fn::Sub": "%s-queue-dlq-function-role-policy-${AWS::StackName}" % queue["name"]}
    policydoc=policy_document(permissions)
    policies=[{"PolicyDocument": policydoc,
               "PolicyName": policyname}]
    props={"AssumeRolePolicyDocument": assume_role_policy_document(),
           "Policies": policies}
    return (resourcename,
            "AWS::IAM::Role",
            props)

@resource
def init_dlq(queue):
    resourcename=H("%s-queue-dlq" % queue["name"])
    props={}
    return (resourcename,
            "AWS::SQS::Queue",
            props)

@resource
def init_dlq_binding(queue, batchsize=1):
    resourcename=H("%s-queue-dlq-binding" % queue["name"])
    funcname={"Ref": H("%s-queue-dlq-function" % queue["name"])}
    sourcearn={"Fn::GetAtt": [H("%s-queue-dlq" % queue["name"]), "Arn"]}
    props={"FunctionName": funcname,
           "EventSourceArn": sourcearn,
           "BatchSize": batchsize}
    return (resourcename,
            "AWS::Lambda::EventSourceMapping",
            props)

@resource
def init_queue(queue):
    resourcename=H("%s-queue" % queue["name"])
    dlqarn={"Fn::GetAtt": [H("%s-queue-dlq" % queue["name"]), "Arn"]}
    redrivepolicy={"deadLetterTargetArn": dlqarn,
                   "maxReceiveCount": 1}
    props={"RedrivePolicy": redrivepolicy}    
    return (resourcename,
            "AWS::SQS::Queue",
            props)

@resource
def init_binding(queue):
    resourcename=H("%s-queue-binding" % queue["name"])
    funcname={"Ref": H("%s-function" % queue["action"])}
    sourcearn={"Fn::GetAtt": [H("%s-queue" % queue["name"]), "Arn"]}
    batchsize = 1 if "batch" not in queue else queue["batch"]    
    props={"FunctionName": funcname,
           "EventSourceArn": sourcearn,
           "BatchSize": batchsize}
    return (resourcename,
            "AWS::Lambda::EventSourceMapping",
            props)

def render_resources(queue):
    resources=[]
    for fn in [init_dlq,
               init_dlq_function,
               init_dlq_function_role,
               init_dlq_binding,
               init_queue,
               init_binding]:
        resource=fn(queue)
        resources.append(resource)
    return dict(resources)

def render_outputs(queue):
    return {H("%s-queue" % queue["name"]): {"Value": {"Ref": H("%s-queue" % queue["name"])}}}

if __name__=="__main__":
    pass
