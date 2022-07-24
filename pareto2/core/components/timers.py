from pareto2.core.components import hungarorise as H
from pareto2.core.components import resource

import json

@resource
def init_rule(timer):
    def init_target(timer):
        id={"Fn::Sub": "%s-timer-rule-${AWS::StackName}" % timer["name"]}
        input=json.dumps(timer["body"])
        arn={"Fn::GetAtt": [H("%s-function" % timer["action"]), "Arn"]}
        return {"Id": id,
                "Input": input,
                "Arn": arn}        
    resourcename=H("%s-timer-rule" % timer["name"])
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
    sourcearn={"Fn::GetAtt": [H("%s-timer-rule" % timer["name"]), "Arn"]}
    funcname={"Ref": H("%s-function" % timer["action"])}
    props={"Action": "lambda:InvokeFunction",
           "Principal": "events.amazonaws.com",
           "FunctionName": funcname,
           "SourceArn": sourcearn}
    return (resourcename,
            "AWS::Lambda::Permission",
            props)

def init_component(timer):
    resources=[]
    for fn in [init_rule,
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
        template.dump_local(template.local_filename)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
