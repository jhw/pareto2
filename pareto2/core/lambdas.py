import importlib, inspect, os, unittest, zipfile

class Lambdas:

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
        
    @property
    def s3_key(self):
        return "lambdas-%s.zip" % self.timestamp
            
    def dump_s3(self, s3, bucketname):
        s3.upload_file(Filename=self.local_filename,
                       Bucket=bucketname,
                       Key=self.s3_key,
                       ExtraArgs={'ContentType': 'application/zip'})

if __name__=="__main__":
    pass
        
