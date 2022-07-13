from pareto2.core import init_template

from pareto2.core.metadata import Metadata
from pareto2.core.template import Template

from pareto2.cli import hungarorise

from datetime import datetime

from pareto2.cli import load_config

import importlib, inspect, os, sys, unittest, zipfile

def filter_tests(root=os.environ["APP_ROOT"]):
    classes=[]
    for parent, _, itemnames in os.walk(root):
        if "__pycache__" in parent:
            continue
        for itemname in itemnames:
            if (not itemname.endswith(".py") or
                itemname=="index.py"):
                continue
            modname="%s.%s" % (parent.replace("/", "."),
                               itemname.split(".")[0])
            mod=importlib.import_module(modname)
            classes+=[obj for name, obj in inspect.getmembers(mod, inspect.isclass)
                      if name.endswith("Test")]
    return classes

def run_tests(tests):
    suite=unittest.TestSuite()
    for test in tests:
        suite.addTest(unittest.makeSuite(test))
    runner=unittest.TextTestRunner()
    result=runner.run(suite)
    if (result.errors!=[] or
        result.failures!=[]):
        raise RuntimeError("unit tests failed")

class Lambdas(list):

    @classmethod
    def initialise(self, md, timestamp, root=os.environ["APP_ROOT"]):
        def filter_paths(root):
            paths, errors = [], []
            for parent, _, itemnames in os.walk(root):
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
        paths, errors = filter_paths(root)
        if errors!=[]:
            raise RuntimeError("; ".join(errors))
        return Lambdas(paths, md.actions, timestamp)

    def __init__(self, paths, actions, timestamp):
        list.__init__(self, paths)
        self.actions=actions
        self.timestamp=timestamp

    def validate_actions(self):
        actionnames=[action["name"]
                     for action in self.actions]
        errors=[]
        for path in self:
            if path.endswith("index.py"):
                actionname="-".join(path.split("/")[:-1])
                if "errors" not in path:
                    if actionname not in actionnames:
                        errors.append(actionname)
        if errors!=[]:
            raise RuntimeError("action not defined for %s" % ", ".join(errors))

    def validate(self):
        self.validate_actions()

    @property
    def s3_key_zip(self):
        return "lambdas-%s.zip" % self.timestamp
    
    @property
    def filename_zip(self):
        return "tmp/%s" % self.s3_key_zip
        
    def dump_zip(self):
        zf=zipfile.ZipFile(self.filename_zip, 'w', zipfile.ZIP_DEFLATED)
        for path in self:
            zf.write(path)
        zf.close()

if __name__=="__main__":
    try:
        if not os.path.exists("tmp"):
            os.mkdir("tmp")
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stage")
        stagename=sys.argv[1]
        config=load_config()
        md=Metadata.initialise(stagename)
        md.validate().expand()
        # run unit tests
        run_tests(filter_tests())
        # initialising/validating lambdas
        timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        lambdas=Lambdas.initialise(md=md,
                                   timestamp=timestamp)
        lambdas.validate()
        lambdas.dump_zip()
        # initialising template
        template=init_template(md,
                               name="main",
                               timestamp=timestamp)
        # updating template with env parameters
        config.update({"StageName": stagename,
                       "ArtifactsKey": lambdas.s3_key_zip})
        layerparams={hungarorise("layer-key-%s" % pkgname): "layer-%s.zip" % pkgname
                     for pkgname in md.actions.packages}
        config.update(layerparams)
        template.update_parameter_defaults(config)
        if not template.are_parameters_complete:
            raise RuntimeError("template is not complete")
        # dump, validate template
        print ("dumping to %s" % template.filename_json)
        template.dump_json(template.filename_json)
        template.validate_root()
        """
        s3=boto3.client("s3")
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
        """
    except RuntimeError as error:
        print ("Error: %s" % str(error))


