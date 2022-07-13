from pareto2.core import init_template

from pareto2.core.metadata import Metadata
from pareto2.core.template import Template

from datetime import datetime

from pareto2.cli import load_config

import os, sys, zipfile

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
        # initialising/validating metadata
        config=load_config()
        md=Metadata.initialise(stagename)
        md.validate().expand()
        # initialising/validating lambdas
        timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        lambdas=Lambdas.initialise(md=md,
                                   timestamp=timestamp)
        lambdas.validate()
        lambdas.dump_zip()
        # initialising/validating template
        template=init_template(md,
                               name="main",
                               timestamp=timestamp)
        print ("dumping to %s" % template.filename_json)
        template.dump_json(template.filename_json)
        template.validate_root()
    except RuntimeError as error:
        print ("Error: %s" % str(error))


