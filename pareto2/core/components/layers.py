from pareto2.core.components import hungarorise as H
from pareto2.core.components import resource

@resource
def init_layer(pkgname):
    resourcename=H("layer-%s" % pkgname)
    content={"S3Bucket": {"Ref": H("artifacts-bucket")},
             "S3Key": {"Ref": H("layer-key-%s" % pkgname)}}
    runtimes=[{"Fn::Sub": "python${RuntimeVersion}"}]
    props={"CompatibleRuntimes": runtimes,
           "Content": content}
    return (resourcename,
            "AWS::Lambda::LayerVersion",
            props)

def init_resources(md):
    return dict([init_layer(pkgname)
                 for pkgname in md.actions.packages])

def update_template(template, md):
    template["Resources"].update(init_resources(md))

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stagename")
        stagename=sys.argv[1]
        from pareto2.core.template import Template
        template=Template("layers")
        from pareto2.core.metadata import Metadata
        md=Metadata.initialise(stagename)
        md.validate().expand()
        update_template(template, md)
        template.dump_yaml(template.filename_yaml)
    except RuntimeError as error:
        print ("Error: %s" % str(error))

        
