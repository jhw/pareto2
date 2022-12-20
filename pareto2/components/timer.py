from pareto2.components import hungarorise as H
from pareto2.components import resource

import json

@resource
def init_timer(timer):
    def init_target(timer):
        id={"Fn::Sub": "%s-timer-${AWS::StackName}" % timer["name"]}
        body=json.dumps(timer["body"])
        arn={"Fn::GetAtt": [H("%s-function" % timer["action"]), "Arn"]}
        return {"Id": id,
                "Input": body,
                "Arn": arn}        
    resourcename=H("%s-timer" % timer["name"])
    target=init_target(timer)
    scheduleexpr="rate(%s)" % timer["rate"]
    props={"Targets": [target],
           "ScheduleExpression": scheduleexpr}
    return (resourcename,
            "AWS::Events::Rule",
            props)

@resource
def init_permission(timer):
    resourcename=H("%s-timer-permission" % timer["name"])
    sourcearn={"Fn::GetAtt": [H("%s-timer" % timer["name"]), "Arn"]}
    funcname={"Ref": H("%s-function" % timer["action"])}
    props={"Action": "lambda:InvokeFunction",
           "Principal": "events.amazonaws.com",
           "FunctionName": funcname,
           "SourceArn": sourcearn}
    return (resourcename,
            "AWS::Lambda::Permission",
            props)

def render_resources(timer):
    resources=[]
    for fn in [init_timer,
               init_permission]:
        resource=fn(timer)
        resources.append(resource)
    return dict(resources)

def render_outputs(timer):
    return {H("%s-timer" % timer["name"]): {"Value": {"Ref": H("%s-timer" % timer["name"])}}}

if __name__=="__main__":
    pass
