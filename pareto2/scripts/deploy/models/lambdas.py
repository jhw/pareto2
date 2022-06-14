import os, zipfile

class Lambdas(list):

    """
    - Lambdas doesn't currently need md, but other similar classes eg Layers take it
    - you can't just look at md.actions here; you need other artifacts eg scrapers, models, yaml files
    """
    
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

    def validate_errors(self):
        paths=[]
        for path in self:
            if path.endswith("index.py"):
                if "errors" in path:
                    paths.append(path)
        if paths==[]:
            raise RuntimeError("errors handler not found")
        elif len(paths) > 1:
            raise RuntimeError("multiple error handlers found")
    
    def validate(self):
        self.validate_actions()
        self.validate_errors()
        
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
    pass

