from pareto2.core.components import hungarorise as H
from pareto2.core.components import resource

@resource
def init_bucket(bucket):
    resourcename=H("%s-bucket" % bucket["name"])
    name={"Fn::Sub": "%s-bucket-${AWS::StackName}-${AWS::Region}" % bucket["name"]}
    notconf={"EventBridgeConfiguration": {"EventBridgeEnabled": True}}
    props={"BucketName": name,
           "NotificationConfiguration": notconf}
    return (resourcename,
            "AWS::S3::Bucket",
            props)

def init_resources(md):
    resources=[]
    for bucket in md["buckets"]:
        resources.append(init_bucket(bucket))
    return dict(resources)

def init_outputs(md):
    return {H("%s-bucket" % bucket["name"]): {"Value": {"Ref": H("%s-bucket" % bucket["name"])}}
            for bucket in md["buckets"]}

def update_template(template, md):
    template.resources.update(init_resources(md))
    template.outputs.update(init_outputs(md))

if __name__=="__main__":
    try:
        from pareto2.cli import load_config
        config=load_config()
        from pareto2.core.template import Template
        template=Template("buckets")
        from pareto2.core.metadata import Metadata
        md=Metadata(config["components"])
        md.validate().expand()
        update_template(template, md)
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
