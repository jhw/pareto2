from pareto2.core.components import hungarorise as H
from pareto2.core.components import resource

"""
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-events-eventbus.html
- Name is a required property
"""

@resource
def init_eventbus(router):
    resourcename=H("%s-router-event-bus" % router["name"])
    name={"Fn::Sub": "%s-router-event-bus-${AWS::StackName}-${AWS::Region}" % router["name"]}
    props={"Name": name}
    return (resourcename, 
            "AWS::Events::EventBus",
            props)

def init_resources(md):
    resources=[]
    for router in md.routers:
        for fn in [init_eventbus]:
            resource=fn(router)
            resources.append(resource)
    return dict(resources)

def init_outputs(md):
    def init_outputs(router, outputs):
        eventbus={"Ref": H("%s-router-event-bus" % router["name"])}
        outputs.update({H("%s-router-event-bus" % router["name"]): {"Value": eventbus}})
    outputs={}
    for router in md.routers:
        init_outputs(router, outputs)
    return outputs
    
def update_template(template, md):
    template.resources.update(init_resources(md))
    template.outputs.update(init_outputs(md))

if __name__=="__main__":
    try:
        from pareto2.core.template import Template
        template=Template("routers")
        from pareto2.core.metadata import Metadata
        md=Metadata.initialise()        
        md.validate().expand()
        update_template(template, md)
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
