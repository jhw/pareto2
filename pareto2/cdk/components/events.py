from pareto2.cdk.components import hungarorise as H
from pareto2.cdk.components import resource

"""
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-events-eventbus.html
- Name is a required property
"""

@resource
def init_event_bus(events):
    resourcename=H("%s-event-bus" % events["name"])
    name={"Fn::Sub": "event-bus-${AWS::StackName}-${AWS::Region}"}
    props={"Name": name}
    return (resourcename, 
            "AWS::Events::EventBus",
            props)

@resource
def init_discoverer(events):
    resourcename=H("%s-discoverer" % events["name"])
    sourcearn={"Fn::GetAtt": [H("%s-event-bus" % events["name"]), "Arn"]}
    props={"SourceArn": sourcearn}
    return (resourcename, 
            "AWS::EventSchemas::Discoverer",
            props)

def init_resources(md):
    resources=[]
    events=md.events
    for fn in [init_event_bus,
               init_discoverer]:
        resource=fn(events)
        resources.append(resource)
    return dict(resources)

def init_outputs(md):
    events=md.events
    eventbus={"Ref": H("%s-event-bus" % events["name"])}
    return {H("%s-event-bus" % events["name"]): {"Value": eventbus}}

def update_template(template, md):
    template["Resources"].update(init_resources(md))
    template["Outputs"].update(init_outputs(md))

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
