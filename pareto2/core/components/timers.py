from pareto2.core.components import hungarorise as H
from pareto2.core.components import uppercase as U
from pareto2.core.components import resource

import json

FunctionCode="""import boto3, json, os

def handler(event, context,
            interval=os.environ["INTERVAL"],
            queueurl=os.environ["QUEUE_URL"]):
    sqs=boto3.client("sqs")
    items=json.loads(event["body"]) # not sure if this is correct
    for i, item in enumerate(items):
        delay=i*int(interval)
        sqs.send_message(QueueUrl=queueurl,
                         DelaySeconds=delay,
                         MessageBody=json.dumps(item))
"""

@resource
def init_rule(timer):
    def init_target(timer):
        id={"Fn::Sub": "%s-timer-rule-${AWS::StackName}" % timer["name"]}
        input=json.dumps(timer["body"])
        arn={"Fn::GetAtt": [H("%s-timer-function" % timer["action"]), "Arn"]}
        return {"Id": id,
                "Input": input,
                "Arn": arn}        
    resourcename=H("%s-timer-rule" % timer["name"])
    target=init_target(timer)
    scheduleexpr={"Fn::Sub": "rate(${%s})" % H("%s-timer-rate" % timer["name"])} # defaults
    props={"Targets": [target],
           "ScheduleExpression": scheduleexpr}
    return (resourcename,
            "AWS::Events::Rule",
            props)

@resource            
def init_function(timer,
                  code=FunctionCode):
    resourcename=H("%s-timer-function" % timer["name"])
    rolename=H("%s-timer-function-role" % timer["name"])
    code={"ZipFile": code}
    runtime={"Fn::Sub": "python${%s}" % H("runtime-version")}
    variables={}
    variables[U(H("queue-url"))]={"Ref": H("%s-timer-queue" % timer["name"])}
    variables[U("interval")]={"Ref": H("%s-timer-interval" % timer["name"])} # defaults
    props={"Role": {"Fn::GetAtt": [rolename, "Arn"]},
           "Code": code,
           "Runtime": runtime,
           "Environment": {"Variables": variables}}
    return (resourcename, 
            "AWS::Lambda::Function",
            props)

@resource
def init_role(timer,
              permissions=["sqs:*", "logs:*"]):
    resourcename=H("%s-timer-function-role" % timer["name"])
    assumerolepolicydoc={"Version": "2012-10-17",
                         "Statement": [{"Action": "sts:AssumeRole",
                                        "Effect": "Allow",
                                        "Principal": {"Service": "lambda.amazonaws.com"}}]}
    policydoc={"Version": "2012-10-17",
               "Statement": [{"Action" : "%s:*" % permission,
                              "Effect": "Allow",
                              "Resource": "*"}
                             for permission in sorted(permissions)]}
    policyname={"Fn::Sub": "%s-timer-function-role-policy-${AWS::StackName}" % timer["name"]}
    policies=[{"PolicyDocument": policydoc,
               "PolicyName": policyname}]
    props={"AssumeRolePolicyDocument": assumerolepolicydoc,
           "Policies": policies}
    return (resourcename,
            "AWS::IAM::Role",
            props)

@resource
def init_queue(timer):
    resourcename=H("%s-timer-queue" % timer["name"])
    props={}
    return (resourcename,
            "AWS::SQS::Queue",
            props)

@resource
def init_binding(timer):
    resourcename=H("%s-timer-queue-binding" % timer["name"])
    funcname={"Ref": H("%s-timer-function" % timer["action"])}
    sourcearn={"Fn::GetAtt": [H("%s-timer-queue" % timer["name"]),
                              "Arn"]}
    props={"FunctionName": funcname,
           "EventSourceArn": sourcearn}
    return (resourcename,
            "AWS::Lambda::EventSourceMapping",
            props)

@resource
def init_permission(timer):
    resourcename=H("%s-timer-permission" % timer["name"])
    sourcearn={"Fn::GetAtt": [H("%s-timer-rule" % timer["name"]), "Arn"]} # CHANGE
    funcname={"Ref": H("%s-timer-function" % timer["action"])}
    props={"Action": "lambda:InvokeFunction",
           "Principal": "events.amazonaws.com", # CHANGE
           "FunctionName": funcname,
           "SourceArn": sourcearn}
    return (resourcename,
            "AWS::Lambda::Permission",
            props)

def init_component(timer):
    resources=[]
    for fn in [init_rule,
               init_function,
               init_role,
               init_queue,
               init_binding,
               init_permission]:
        resource=fn(timer)
        resources.append(resource)
    return resources

def init_resources(md):
    resources=[]
    for timer in md.timers:
        component=init_component(timer)
        resources+=component
    return dict(resources)

def update_template(template, md):
    template.resources.update(init_resources(md))

if __name__=="__main__":
    try:
        from pareto2.core.template import Template
        template=Template("timers")
        from pareto2.core.metadata import Metadata
        md=Metadata.initialise()
        md.validate().expand()
        update_template(template, md)
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
