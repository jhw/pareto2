from pareto2.core.template import Template
from pareto2.core.metadata import Metadata

from pareto2.cli import hungarorise

from botocore.exceptions import ClientError, WaiterError

from pareto2.cli import load_config

import boto3, json, os, sys

class Layers(list):

    @classmethod
    def initialise(self, md):
        return Layers(md.actions.packages)
    
    def __init__(self, items=[]):
        list.__init__(self, items)

    @property
    def parameters(self):
        return {hungarorise("layer-key-%s" % pkgname): "layer-%s.zip" % pkgname
                for pkgname in self}

class Parameters(dict):

    @classmethod
    def initialise(self, items):
        params=Parameters()
        for item in items:
            params.update(item)
        return params
    
    def __init__(self, items={}):
        dict.__init__(self, items)

    def validate(self, template):
        errors=[]
        for paramname in self:
            if paramname not in template["Parameters"]:
                errors.append("unknown parameter %s" % paramname)
        for paramname, param in template["Parameters"].items():
            if ("Default" not in param and
                paramname not in self):
                errors.append("missing parameter %s" % paramname)
        if errors!=[]:
            raise RuntimeError("; ".join(errors))
        
    def render(self):
        return [{"ParameterKey": k,
                 "ParameterValue": str(v)} # NB CF requires all values as strings
                for k, v in self.items()]

def deploy_stack(cf, config, params, template):
    def stack_exists(stackname):
        stacknames=[stack["StackName"]
                    for stack in cf.describe_stacks()["Stacks"]]
        return stackname in stacknames
    stackname="%s-%s" % (config["AppName"],
                         config["StageName"])
    action="update" if stack_exists(stackname) else "create"
    
    fn=getattr(cf, "%s_stack" % action)
    url=template.url(config["ArtifactsBucket"])
    fn(StackName=stackname,
       Parameters=params.render(),
       TemplateURL=url,
       Capabilities=["CAPABILITY_IAM"])
    waiter=cf.get_waiter("stack_%s_complete" % action)
    waiter.wait(StackName=stackname)

if __name__=="__main__":
    try:
        if len(sys.argv) < 3:
            raise RuntimeError("please enter stage, template")
        stagename, filename = sys.argv[1:3]
        if not os.path.exists(filename):
            raise RuntimeError("file does not exist")
        template=Template(items=json.loads(open(filename).read()))
        config=load_config()
        md=Metadata.initialise(stagename)
        timestamp="-".join(filename.split(".")[0].split("-")[-6:])
        artifactskey="lambdas-%s.zip" % timestamp
        config.update({"StageName": stagename,
                       "ArtifactsKey": artifactskey})
        layers=Layers.initialise(md)
        params=Parameters.initialise([config,
                                      layers.parameters])
        params.validate(template)
        print (params)
        """
        cf=boto3.client("cloudformation")
        print ("pushing lambdas -> %s" % lambdas.s3_key_zip)
        s3.upload_file(Filename=lambdas.filename_zip,
                       Bucket=config["ArtifactsBucket"],
                       Key=lambdas.s3_key_zip,
                       ExtraArgs={'ContentType': 'application/zip'})
        print ("pushing template -> %s" % template.s3_key_json)
        s3.put_object(Bucket=config["ArtifactsBucket"],
                      Key=template.s3_key_json,
                      Body=template.to_json(),
                      ContentType="application/json")
        print ("deploying stack")
        deploy_stack(config=config,
                     params=params,
                     template=template,
                     cf=cf)
        """
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))
    except WaiterError as error:
        print ("Error: %s" % str(error))

