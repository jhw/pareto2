from pareto2.cdk.components import hungarorise as H
from pareto2.cdk.components import resource

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
    template["Resources"].update(init_resources(md))
    template["Outputs"].update(init_outputs(md))

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stagename")
        stagename=sys.argv[1]
        from pareto2.cdk.template import Template
        template=Template("router")
        from pareto2.cdk.metadata import Metadata
        md=Metadata.initialise(stagename)        
        md.validate().expand()
        update_template(template, md)
        template.dump_yaml(template.filename_yaml)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
