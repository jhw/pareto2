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

def init_resources(buckets):
    resources=[]
    for bucket in buckets:
        resources.append(init_bucket(bucket))
    return dict(resources)

def init_outputs(buckets):
    return {H("%s-bucket" % bucket["name"]): {"Value": {"Ref": H("%s-bucket" % bucket["name"])}}
            for bucket in buckets}

if __name__=="__main__":
    try:
        from pareto2.core.dsl import Config
        config=Config.initialise()
        from pareto2.core.template import Template
        template=Template("buckets")
        template.resources.update(init_resources(config["components"]["buckets"]))
        template.outputs.update(init_outputs(config["components"]["buckets"]))
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
