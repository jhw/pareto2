from pareto2.core import init_template
from pareto2.core.metadata import Metadata
from pareto2.core.template import Template
from pareto2.cli import hungarorise, load_config

import boto3, importlib, inspect, os, unittest, zipfile

from datetime import datetime

class Artifacts:

    def __init__(self, timestamp, root=os.environ["APP_ROOT"]):
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
    
    def validate_actions(self, md):
        actionnames=[action["name"]
                     for action in md.actions]
        errors=[]
        for path in self.paths:
            if path.endswith("index.py"):
                actionname="-".join(path.split("/")[:-1])
                if "errors" not in path:
                    if actionname not in actionnames:
                        errors.append(actionname)
        if errors!=[]:
            raise RuntimeError("action not defined for %s" % ", ".join(errors))

    def validate(self, md):
        self.validate_actions(md)

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
    def local_filename(self):
        return "tmp/%s" % self.s3_key
        
    def dump_local(self):
        zf=zipfile.ZipFile(self.local_filename, 'w', zipfile.ZIP_DEFLATED)
        for path in self.paths:
            zf.write(path)
        zf.close()
        
    def build(self, md, run_tests=True, validate=True):
        if run_tests:
            self.run_tests()
        if validate:            
            self.validate(md)
        self.dump_local()
        
    @property
    def s3_key(self):
        return "lambdas-%s.zip" % self.timestamp
            
    def dump_s3(self, s3, bucketname):
        s3.upload_file(Filename=self.local_filename,
                       Bucket=bucketname,
                       Key=self.s3_key,
                       ExtraArgs={'ContentType': 'application/zip'})
        
if __name__=="__main__":
    try:
        if not os.path.exists("tmp"):
            os.mkdir("tmp")
        config=load_config()
        md=Metadata.initialise()
        md.validate().expand()
        timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        artifacts=Artifacts(timestamp=timestamp)
        artifacts.build(md)
        template=init_template(md,
                               name="main",
                               timestamp=timestamp)
        config.update({"ArtifactsKey": artifacts.s3_key})
        # START TEMP LAYER STUFF
        layerparams={hungarorise("layer-key-%s" % pkgname): "layer-%s.zip" % pkgname
                     for pkgname in md.actions.packages}
        config.update(layerparams)
        # END TEMP LAYER STUFF
        template.parameters.update_defaults(config)
        required=template.parameters.required_keys
        if "StageName" not in required:
            raise RuntimeError("StageName not specified as required key")
        if len(required)!=1:
            raise RuntimeError("Invalid required parameters - %s" % ", ".join(required))
        template.dump_local()
        template.validate_root()
        s3=boto3.client("s3")
        print ("pushing %s" % artifacts.s3_key)
        artifacts.dump_s3(s3, config["ArtifactsBucket"])
        print ("pushing %s" % template.s3_key)
        template.dump_s3(s3, config["ArtifactsBucket"])
    except RuntimeError as error:
        print ("Error: %s" % str(error))


