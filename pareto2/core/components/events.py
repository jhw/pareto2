from pareto2.core.components import hungarorise as H
from pareto2.core.components import resource

import json

"""
- event.router is optional because absence of router implies use of default router
- and many services use default router and can't be changed eg (1) s3 notifications, eg (2) codebuild notifications
"""

@resource
def init_rule(event):
    def init_target(event):
        id={"Fn::Sub": "%s-event-rule-${AWS::StackName}" % event["name"]}
        arn={"Fn::GetAtt": [H("%s-function" % event["target"]), "Arn"]}
        return {"Id": id,
                "Arn": arn}
    resourcename=H("%s-event-rule" % event["name"])
    pattern={"detail": event["pattern"]}
    if "source" in event:
        if "action" in event["source"]:
            pattern["source"]=[{"Ref": H("%s-function" % event["source"]["action"])}]
        elif "bucket" in event["source"]:
            # pattern["source"]=[{"Ref": H("%s-bucket" % event["source"]["bucket"])}]
            pattern["detail"].setdefault("bucket", {})
            pattern["detail"]["bucket"]["name"]=[{"Ref": H("%s-bucket" % event["source"]["bucket"])}]
        elif "table" in event["source"]:
            pattern["source"]=[{"Ref": H("%s-table-function" % event["source"]["table"])}]
    target=init_target(event)
    props={"EventPattern": pattern,
           "Targets": [target],
           "State": "ENABLED"}
    if "router" in event:
        eventbusname={"Ref": H("%s-router-event-bus" % event["router"])}
        props["EventBusName"]=eventbusname
    return (resourcename,
            "AWS::Events::Rule",
            props)

@resource
def init_permission(event):
    resourcename=H("%s-event-permission" % event["name"])
    sourcearn={"Fn::GetAtt": [H("%s-event-rule" % event["name"]), "Arn"]}
    funcname={"Ref": H("%s-function" % event["target"])}
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
        from pareto2.core.template import Template
        template=Template("events")
        from pareto2.core.metadata import Metadata
        md=Metadata.initialise()
        md.validate().expand()
        update_template(template, md)
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
