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
    pass
