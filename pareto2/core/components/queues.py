from pareto2.core.components import hungarorise as H
from pareto2.core.components import resource

@resource
def init_queue(queue):
    resourcename=H("%s-queue" % queue["name"])
    props={}
    return (resourcename,
            "AWS::SQS::Queue",
            props)

@resource
def init_binding(queue):
    resourcename=H("%s-queue-binding" % queue["name"])
    funcname={"Ref": H("%s-function" % queue["action"])}
    sourcearn={"Fn::GetAtt": [H("%s-queue" % queue["name"]),
                              "Arn"]}
    props={"FunctionName": funcname,
           "EventSourceArn": sourcearn}
    return (resourcename,
            "AWS::Lambda::EventSourceMapping",
            props)

def init_component(queue):
    resources=[]
    for fn in [init_queue,
               init_binding]:
        resource=fn(queue)
        resources.append(resource)
    return resources

def init_resources(md):
    resources=[]
    for queue in md.queues:
        component=init_component(queue)
        resources+=component
    return dict(resources)

def update_template(template, md):
    template.resources.update(init_resources(md))

if __name__=="__main__":
    try:
        from pareto2.core.template import Template
        template=Template("queues")
        from pareto2.core.metadata import Metadata
        md=Metadata.initialise()
        md.validate().expand()
        update_template(template, md)
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
