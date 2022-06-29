from pareto2.cdk.metadata import Metadata
from pareto2.cdk.template import Template

from pareto2.scripts.deploy.models.lambdas import Lambdas
from pareto2.scripts.deploy.models.layers import Layers
from pareto2.scripts.deploy.models.parameters import Parameters

from botocore.exceptions import ClientError, WaiterError

import boto3, yaml

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
        import os, sys
        if not os.path.exists("tmp"):
            os.mkdir("tmp")
        if len(sys.argv) < 3:
            raise RuntimeError("please enter deploy stage, flag (true|false)")
        stagename, flag = sys.argv[1:3]
        if flag.lower() not in ["true", "false"]:
            raise RuntimeError("deploy flag is invalid")
        flag=eval(flag.capitalize())        
        print ("initialising/validating metadata")
        from datetime import datetime
        timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        from pareto2.scripts import load_config
        config=load_config()
        md=Metadata.initialise(stagename)
        md.validate().expand()
        print ("initialising/validating lambdas")
        lambdas=Lambdas.initialise(md=md,
                                   timestamp=timestamp)
        lambdas.validate()
        lambdas.dump_zip()
        config.update({"StageName": stagename,
                       "ArtifactsKey": lambdas.s3_key_zip})
        print ("initialising/validating layers")
        s3=boto3.client("s3")
        layers=Layers.initialise(md)
        """
        layers.validate(s3, config)
        """
        print ("initialising/validating template")
        from pareto2.cdk import init_template
        template=init_template(md,
                               name="main",
                               timestamp=timestamp)
        print ()
        print (yaml.safe_dump(template.metrics,
                              default_flow_style=False))
        template.dump_yaml(template.filename_yaml)
        template.validate_root()
        params=Parameters.initialise([config,
                                      layers.parameters])
        params.validate(template)
        if flag:
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
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))
    except WaiterError as error:
        print ("Error: %s" % str(error))

