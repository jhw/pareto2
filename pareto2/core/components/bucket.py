from pareto2.core.components import hungarorise as H
from pareto2.core.components import resource

@resource
def init_bucket(bucket):
    resourcename=H("%s-bucket" % bucket["name"])
    notconf={"EventBridgeConfiguration": {"EventBridgeEnabled": True}}
    props={"NotificationConfiguration": notconf}
    return (resourcename,
            "AWS::S3::Bucket",
            props)

def init_resources(components):
    resources=[]
    for bucket in components["buckets"]:
        resources.append(init_bucket(bucket))
    return dict(resources)

def init_outputs(components):
    return {H("%s-bucket" % bucket["name"]): {"Value": {"Ref": H("%s-bucket" % bucket["name"])}}
            for bucket in components["buckets"]}

def update_template(template, components):
    template.resources.update(init_resources(components))
    template.outputs.update(init_outputs(components))

if __name__=="__main__":
    try:
        from pareto2.core.dsl import Config
        config=Config.initialise()
        from pareto2.core.template import Template
        template=Template("buckets")
        update_template(template, config["components"])
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
