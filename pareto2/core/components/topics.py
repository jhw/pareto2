from pareto2.core.components import hungarorise as H
from pareto2.core.components import resource

@resource
def init_topic(topic):
    resourcename=H("%s-topic" % topic["name"])
    props={}
    return (resourcename,
            "AWS::S3::Topic",
            props)

def init_resources(md):
    resources=[]
    for topic in md.topics:
        resources.append(init_topic(topic))
    return dict(resources)

def init_outputs(md):
    return {H("%s-topic" % topic["name"]): {"Value": {"Ref": H("%s-topic" % topic["name"])}}
            for topic in md.topics}

def update_template(template, md):
    template.resources.update(init_resources(md))
    template.outputs.update(init_outputs(md))

if __name__=="__main__":
    try:
        from pareto2.core.template import Template
        template=Template("topics")
        from pareto2.core.metadata import Metadata
        md=Metadata.initialise()
        md.validate().expand()
        update_template(template, md)
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
