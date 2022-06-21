from pareto2.cdk.components import hungarorise as H
from pareto2.cdk.components import resource

import json

@resource
def init_rule(router, action, event, i):
    def init_target(action, event, i):
        id={"Fn::Sub": "%s-rule-%i-${AWS::StackName}" % (action["name"], i)}
        arn={"Fn::GetAtt": [H("%s-function" % action["name"]), "Arn"]}
        return {"Id": id,
                "Arn": arn}
    resourcename=H("%s-rule-%i" % (action["name"], i))
    pattern={"detail": event["pattern"]}
    if "source" in event:
        pattern["source"]=[{"Ref": H("%s-function" % event["source"])}]
    target=init_target(action, event, i)
    eventbusname={"Ref": H("%s-event-bus" % router["name"])}
    props={"EventBusName": eventbusname,
           "EventPattern": pattern,
           "Targets": [target],
           "State": "ENABLED"}
    return (resourcename,
            "AWS::Events::Rule",
            props)

@resource
def init_permission(router, action, event, i):
    resourcename=H("%s-permission-%i" % (action["name"], i))
    sourcearn={"Fn::GetAtt": [H("%s-rule-%i" % (action["name"], i)), "Arn"]}
    funcname={"Ref": H("%s-function" % action["name"])}
    props={"Action": "lambda:InvokeFunction",
           "Principal": "events.amazonaws.com",
           "FunctionName": funcname,
           "SourceArn": sourcearn}
    return (resourcename,
            "AWS::Lambda::Permission",
            props)

def init_component(router, action, event, i):
    resources=[]
    for fn in [init_rule,
               init_permission]:
        resource=fn(router, action, event, i)
        resources.append(resource)
    return resources

def init_resources(md):
    resources=[]
    # START TEMP CODE
    router=md.routers[0]
    # END TEMP CODE
    for action in md.actions:
        if "events" in action:
            for i, event in enumerate(action["events"]):
                component=init_component(router, action, event, i+1)
                resources+=component
    return dict(resources)

def update_template(template, md):
    template["Resources"].update(init_resources(md))

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stagename")
        stagename=sys.argv[1]
        from pareto2.cdk.template import Template
        template=Template("events")
        from pareto2.cdk.metadata import Metadata
        md=Metadata.initialise(stagename)
        md.validate().expand()
        update_template(template, md)
        template.dump_yaml(template.filename_yaml)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
