from pareto2.core.components import hungarorise as H
from pareto2.core.components import uppercase as U
from pareto2.core.components import resource

import json, math

MicroFunctionCode="""import boto3, json, os

def handler(event, context,
            n=os.environ["N"],
            interval=os.environ["INTERVAL"],
            queueurl=os.environ["QUEUE_URL"]):
    sqs=boto3.client("sqs")
    for i in range(int(n)):
        delay=i*int(interval)
        sqs.send_message(QueueUrl=queueurl,
                         DelaySeconds=delay,
                         MessageBody=json.dumps(event))
"""

MicroRate=300

MemorySize, Timeout = "small", "short"

@resource
def init_rule(timer, rate):
    def format_schedule(rate):
        minutes=int(rate/60)
        suffix="minute" if minutes==1 else "minutes"
        return "rate(%i %s)" % (minutes, suffix)
    def init_target(timer):
        targetid={"Fn::Sub": "%s-timer-rule-${AWS::StackName}" % timer["name"]}
        body=json.dumps(timer["body"])
        arn={"Fn::GetAtt": [H("%s-timer-function" % timer["name"]), "Arn"]}
        return {"Id": targetid,
                "Input": body,
                "Arn": arn}        
    resourcename=H("%s-timer-rule" % timer["name"])
    target=init_target(timer)
    scheduleexpr=format_schedule(rate)
    props={"Targets": [target],
           "ScheduleExpression": scheduleexpr}
    return (resourcename,
            "AWS::Events::Rule",
            props)

def init_micro_rule(timer, rate=MicroRate):
    return init_rule(timer, rate)

@resource
def init_permission(timer):
    resourcename=H("%s-timer-permission" % timer["name"])
    sourcearn={"Fn::GetAtt": [H("%s-timer-rule" % timer["name"]), "Arn"]}
    funcname={"Ref": H("%s-timer-function" % timer["name"])}
    props={"Action": "lambda:InvokeFunction",
           "Principal": "events.amazonaws.com",
           "FunctionName": funcname,
           "SourceArn": sourcearn}
    return (resourcename,
            "AWS::Lambda::Permission",
            props)

@resource            
def init_micro_function(timer,
                        rate=MicroRate,
                        code=MicroFunctionCode,
                        memorysize=MemorySize,
                        timeout=Timeout):
    resourcename=H("%s-timer-function" % timer["name"])
    rolename=H("%s-timer-function-role" % timer["name"])
    code={"ZipFile": code}
    runtime={"Fn::Sub": "python${%s}" % H("runtime-version")}
    memorysize=H("memory-size-%s" % memorysize)
    timeout=H("timeout-%s" % timeout)
    n=int(math.floor(rate/timer["interval"]))
    variables={}
    variables[U("queue-url")]={"Ref": H("%s-timer-queue" % timer["name"])}
    variables[U("interval")]=str(timer["interval"])
    variables[U("n")]=str(n)
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
def init_role(timer,
              permissions=["sqs", "logs"]):
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
    funcname={"Ref": H("%s-function" % timer["action"])}
    sourcearn={"Fn::GetAtt": [H("%s-timer-queue" % timer["name"]),
                              "Arn"]}
    props={"FunctionName": funcname,
           "EventSourceArn": sourcearn}
    return (resourcename,
            "AWS::Lambda::EventSourceMapping",
            props)

def init_micro_component(timer):
    resources=[]
    for fn in [init_micro_rule,
               init_permission,
               init_micro_function,
               init_role,
               init_queue,
               init_binding]:
        resource=fn(timer)
        resources.append(resource)
    return resources

def init_resources(md):
    resources=[]
    for timer in md["timers"]:
        component=init_micro_component(timer)
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
