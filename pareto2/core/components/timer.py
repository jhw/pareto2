from pareto2.core.components import hungarorise as H
from pareto2.core.components import uppercase as U
from pareto2.core.components import resource

import json, math

SchedulerFunctionCode="""import boto3, datetime, json, os

def handler(event, context,
            n=os.environ["NUMBER"],
            interval=os.environ["INTERVAL"],
            queueurl=os.environ["QUEUE_URL"]):
    print ("%s -> %s" % (datetime.datetime.now(), event))
    interval, n = int(interval), int(n)
    sqs=boto3.client("sqs")
    for i in range(n):
        delay=i*interval
        sqs.send_message(QueueUrl=queueurl,
                         DelaySeconds=delay,
                         MessageBody=json.dumps(event))
"""

"""
- SchedulerRate could be longer but it will be #{SchedulerRate} seconds before the first timer is called
- possible tradeoff between cost of events rule execution vs cost of sqs message execution
"""

SchedulerMemorySize, SchedulerTimeout = "small", "short"

@resource
def init_rule(timer):
    def format_schedule(minutes):
        suffix="minute" if minutes==1 else "minutes"
        return "rate(%i %s)" % (minutes, suffix)
    def init_target(timer):
        targetid={"Fn::Sub": "%s-timer-rule-${AWS::StackName}" % timer["name"]}
        body=json.dumps(timer["body"])
        arn={"Fn::GetAtt": [H("%s-timer-scheduler-function" % timer["name"]), "Arn"]}
        return {"Id": targetid,
                "Input": body,
                "Arn": arn}        
    resourcename=H("%s-timer-rule" % timer["name"])
    target=init_target(timer)
    minutes=int(math.ceil(timer["interval"]/60))
    scheduleexpr=format_schedule(minutes)
    props={"Targets": [target],
           "ScheduleExpression": scheduleexpr}
    return (resourcename,
            "AWS::Events::Rule",
            props)

@resource
def init_permission(timer):
    resourcename=H("%s-timer-permission" % timer["name"])
    sourcearn={"Fn::GetAtt": [H("%s-timer-rule" % timer["name"]), "Arn"]}
    funcname={"Ref": H("%s-timer-scheduler-function" % timer["name"])}
    props={"Action": "lambda:InvokeFunction",
           "Principal": "events.amazonaws.com",
           "FunctionName": funcname,
           "SourceArn": sourcearn}
    return (resourcename,
            "AWS::Lambda::Permission",
            props)

@resource            
def init_function(timer,
                  code=SchedulerFunctionCode,
                  memorysize=SchedulerMemorySize,
                  timeout=SchedulerTimeout):
    resourcename=H("%s-timer-scheduler-function" % timer["name"])
    rolename=H("%s-timer-scheduler-function-role" % timer["name"])
    code={"ZipFile": code}
    runtime={"Fn::Sub": "python${%s}" % H("runtime-version")}
    memorysize=H("memory-size-%s" % memorysize)
    timeout=H("timeout-%s" % timeout)
    minutes=int(math.ceil(timer["interval"]/60))
    n=int(math.floor(60/timer["interval"])) if minutes==1 else 1
    variables={}
    variables[U("queue-url")]={"Ref": H("%s-timer-queue" % timer["name"])}
    variables[U("interval")]=str(timer["interval"])
    variables[U("number")]=str(n)
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
    resourcename=H("%s-timer-scheduler-function-role" % timer["name"])
    assumerolepolicydoc={"Version": "2012-10-17",
                         "Statement": [{"Action": "sts:AssumeRole",
                                        "Effect": "Allow",
                                        "Principal": {"Service": "lambda.amazonaws.com"}}]}
    policydoc={"Version": "2012-10-17",
               "Statement": [{"Action" : "%s:*" % permission,
                              "Effect": "Allow",
                              "Resource": "*"}
                             for permission in sorted(permissions)]}
    policyname={"Fn::Sub": "%s-timer-scheduler-function-role-policy-${AWS::StackName}" % timer["name"]}
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

def init_resources(timer):
    resources=[]
    for fn in [init_rule,
               init_permission,
               init_function,
               init_role,
               init_queue,
               init_binding]:
        resource=fn(timer)
        resources.append(resource)
    return dict(resources)

def init_outputs(timers):
    return {}

if __name__=="__main__":
    try:
        from pareto2.core.dsl import Config
        config=Config.initialise()
        from pareto2.core.template import Template
        template=Template("timers")
        for timer in config["components"]["timers"]:
            template.resources.update(init_resources(timer))
            template.outputs.update(init_outputs(timer))
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
