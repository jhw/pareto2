from pareto2.components import hungarorise as H
from pareto2.components import resource

@resource
def init_bucket(bucket):
    resourcename=H("%s-bucket" % bucket["name"])
    notconf={"EventBridgeConfiguration": {"EventBridgeEnabled": True}}
    props={"NotificationConfiguration": notconf}
    return (resourcename,
            "AWS::S3::Bucket",
            props)

def render_resources(bucket):
    resources=[]
    resources.append(init_bucket(bucket))
    return dict(resources)

def render_outputs(bucket):
    return {H("%s-bucket" % bucket["name"]): {"Value": {"Ref": H("%s-bucket" % bucket["name"])}}}

if __name__=="__main__":
    try:
        from pareto2.dsl import Config
        config=Config.init_file(filename="demo.yaml")
        from pareto2.template import Template
        template=Template()
        for bucket in config["components"].buckets:
            template.resources.update(render_resources(bucket))
            template.outputs.update(render_outputs(bucket))
        print (template.render())
    except RuntimeError as error:
        print ("Error: %s" % str(error))
