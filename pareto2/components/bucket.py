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
        import os, sys
        filename=sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
        if not os.path.exists(filename):
            raise RuntimeError("%s does not exist" % filename)
        from pareto2.dsl import Config
        config=Config.init_file(filename=filename)
        from pareto2.template import Template
        template=Template()
        for bucket in config["components"].buckets:
            template.resources.update(render_resources(bucket))
            template.outputs.update(render_outputs(bucket))
        print (template.render())
        print ()
        template.init_implied_parameters()
        for validator in [template.parameters.validate,
                          template.validate]:
            try:
                validator()
            except RuntimeError as error:
                print ("Warning: %s" % str(error))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
