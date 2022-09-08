from pareto2.cli.deploy import *

from pareto2.core.dsl import Config
from pareto2.core.template import Template

from botocore.exceptions import ClientError

from datetime import datetime

import boto3, importlib, inspect, io, os, unittest, zipfile

class Lambdas:

    def __init__(self, root, timestamp):
        self.timestamp=timestamp
        self.root=root
        paths, errors = self.filter_paths()
        if errors!=[]:
            raise RuntimeError("; ".join(errors))
        self.paths=paths
        self.tests=self.filter_tests()

    def filter_paths(self):
        paths, errors = [], []
        for parent, _, itemnames in os.walk(self.root):
            if ("__pycache__" in parent or
                "tests" in parent):
                continue
            for itemname in itemnames:
                path="%s/%s" % (parent, itemname)
                if not (itemname in ["test.py"] or
                        itemname.endswith(".pyc")):
                    paths.append(path)
                if itemname not in ["index.py",
                                    "test.py"]:
                    text=open(path).read()
                    if "os.environ" in text:
                        errors.append("invalid os.environ ref in %s" % path)
        return paths, errors

    def filter_tests(self):
        classes=[]
        for parent, _, itemnames in os.walk(self.root):
            if "__pycache__" in parent:
                continue
            for itemname in itemnames:
                if (not itemname.endswith(".py") or
                    itemname=="index.py"):
                    continue
                modname="%s.%s" % (parent.replace("/", "."),
                                   itemname.split(".")[0])
                mod=importlib.import_module(modname)
                classes+=[obj for name, obj in inspect.getmembers(mod,
                                                                  inspect.isclass)
                          if name.endswith("Test")]
        return classes
    
    def validate_actions(self, components):
        actionnames=[action["name"]
                     for action in components.actions]
        errors=[]
        for path in self.paths:
            if path.endswith("index.py"):
                actionname="-".join(path.split("/")[:-1])
                if "errors" not in path:
                    if actionname not in actionnames:
                        errors.append(actionname)
        if errors!=[]:
            raise RuntimeError("action not defined for %s" % ", ".join(errors))

    def validate(self, components):
        self.validate_actions(components)

    def run_tests(self):
        suite=unittest.TestSuite()
        for test in self.tests:
            suite.addTest(unittest.makeSuite(test))
        runner=unittest.TextTestRunner()
        result=runner.run(suite)
        if (result.errors!=[] or
            result.failures!=[]):
            raise RuntimeError("unit tests failed")

    @property
    def zipped_data(self):
        buf=io.BytesIO()
        zf=zipfile.ZipFile(buf, 'a', zipfile.ZIP_DEFLATED, False)
        for path in self.paths:
            zf.write(path)
        zf.close()
        return buf.getvalue()
            
    @property
    def s3_key(self):
        return "lambdas-%s.zip" % self.timestamp
            
    def dump_s3(self, s3, bucketname):
        s3.put_object(Bucket=bucketname,
                      Key=self.s3_key,
                      Body=self.zipped_data,
                      ContentType="application/zip")

class Artifacts:

    def __init__(self, config, root, s3,
                 timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")):
        self.config=config
        self.root=root
        self.s3=s3
        self.timestamp=timestamp

    def build_lambdas(self, run_tests):
        lambdas=Lambdas(self.root, self.timestamp)
        if run_tests:
            lambdas.run_tests() # raises RuntimeError on failure
        lambdas.validate(self.config["components"])
        bucketname=self.config["globals"]["artifacts-bucket"]
        lambdas.dump_s3(self.s3, bucketname)
        return lambdas

    """
    - NB validation occurs after s3 push so any errors are visible
    """
        
    def build_template(self,
                       name,
                       lambdas):
        template=self.config.spawn_template(name=name,
                                            timestamp=self.timestamp)
        template.init_implied_parameters()
        values=self.config.parameters
        values["ArtifactsKey"]=lambdas.s3_key
        template.parameters.update_defaults(values)
        template.dump_s3(self.s3, self.config["globals"]["artifacts-bucket"])
        template.parameters.validate()
        template.validate_root()

    def build(self,
              template_name="template",
              run_tests=True):
        lambdas=self.build_lambdas(run_tests)
        self.build_template(name=template_name,
                            lambdas=lambdas)

if __name__=="__main__":
    try:
        config=Config.initialise()
        appname=os.environ["PARETO2_APP_NAME"]
        s3=boto3.client("s3")
        artifacts=Artifacts(config=config,
                            root=appname,
                            s3=s3)        
        artifacts.build()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))


