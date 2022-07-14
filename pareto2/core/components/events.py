from pareto2.core.components import hungarorise as H
from pareto2.core.components import resource

import json

@resource
def init_rule(event):
    def init_target(event):
        id={"Fn::Sub": "%s-event-rule-${AWS::StackName}" % event["name"]}
        arn={"Fn::GetAtt": [H("%s-function" % event["action"]), "Arn"]}
        return {"Id": id,
                "Arn": arn}
    resourcename=H("%s-event-rule" % event["name"])
    pattern={"detail": event["pattern"]}
    if "source" in event:
        pattern["source"]=[{"Ref": H("%s-function" % event["source"])}]
    target=init_target(event)
    eventbusname={"Ref": H("%s-router-event-bus" % event["router"])}
    props={"EventBusName": eventbusname,
           "EventPattern": pattern,
           "Targets": [target],
           "State": "ENABLED"}
    return (resourcename,
            "AWS::Events::Rule",
            props)

@resource
def init_permission(event):
    resourcename=H("%s-event-permission" % event["name"])
    sourcearn={"Fn::GetAtt": [H("%s-event-rule" % event["name"]), "Arn"]}
    funcname={"Ref": H("%s-function" % event["action"])}
    props={"Action": "lambda:InvokeFunction",
           "Principal": "events.amazonaws.com",
           "FunctionName": funcname,
           "SourceArn": sourcearn}
    return (resourcename,
            "AWS::Lambda::Permission",
            props)

def init_component(event):
    resources=[]
    for fn in [init_rule,
               init_permission]:
        resource=fn(event)
        resources.append(resource)
    return resources

def init_resources(md):
    resources=[]
    for event in md.events:
        component=init_component(event)
        resources+=component
    return dict(resources)

def update_template(template, md):
    template.resources.update(init_resources(md))

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stagename")
        stagename=sys.argv[1]
        from pareto2.core.template import Template
        template=Template("events")
        from pareto2.core.metadata import Metadata
        md=Metadata.initialise(stagename)
        md.validate().expand()
        update_template(template, md)
        template.dump_json(template.filename)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
