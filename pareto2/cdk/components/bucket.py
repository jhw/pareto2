from pareto2.cdk.components import hungarorise as H
from pareto2.cdk.components import resource

"""
- https://aws.amazon.com/premiumsupport/knowledge-center/unable-validate-circular-dependency-cloudformation/
- https://stackoverflow.com/questions/69455149/s3-notificationconfiguration-unable-to-validate-destination-configuration/69457265
- BucketName must be defined
- SourceArn must be defined as a String with BucketName suffix (and not include a Ref to bucket)
- Bucket DependsOn FunctionPermission
- note also that Region added to bucket name as best practice, as I think bucket names are global
"""

@resource
def init_bucket(bucket):
    resourcename=H(bucket["name"])    
    funcarn={"Fn::GetAtt": [H("%s-function" % bucket["name"]), "Arn"]}
    lambdaconf=[{"Event": "s3:ObjectCreated:*",
                 "Function": funcarn}]
    name={"Fn::Sub": "%s-${AWS::StackName}-${AWS::Region}" % bucket["name"]}
    props={"NotificationConfiguration": {"LambdaConfigurations": lambdaconf},
           "BucketName": name}
    depends=[H("%s-permission" % bucket["name"])]
    return (resourcename,
            "AWS::S3::Bucket",
            props,
            depends)

@resource
def init_permission(bucket):
    resourcename=H("%s-permission" % bucket["name"])
    sourcearn={"Fn::Sub": "arn:aws:s3:::%s-${AWS::StackName}-${AWS::Region}" % bucket["name"]}
    funcname={"Ref": H("%s-function" % bucket["name"])}
    props={"Action": "lambda:InvokeFunction",
           "Principal": "s3.amazonaws.com",
           "SourceArn": sourcearn,
           "SourceAccount": {"Ref": "AWS::AccountId"},
           "FunctionName": funcname}
    return (resourcename,
            "AWS::Lambda::Permission",
            props)

def init_resources(md):
    return dict([fn(bucket)
                 for fn in [init_bucket,
                            init_permission]
                 for bucket in md.buckets])

def init_outputs(md):
    return {H(bucket["name"]): {"Value": {"Ref": H(bucket["name"])}}
            for bucket in md.buckets}

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
        template=Template("bucket")
        from pareto2.cdk.metadata import Metadata
        md=Metadata.initialise(stagename)        
        md.validate().expand()
        update_template(template, md)
        template.dump_yaml(template.filename_yaml)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
