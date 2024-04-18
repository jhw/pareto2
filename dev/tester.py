"""
infra:
  events:
  - name: tester
    pattern:
      eventName:
      - INSERT
      sk:
      - EVENT
      records:
        dynamodb:
          NewImage:
            event-stage:
              S: 
              - dslrunner
            event-status:
              S: 
              - STAGE_COMPLETE
    source:
      name: expander2
      type: table
  layers: 
  - layman2-expander-app-env
  - layman2-expander-pipeline7
  permissions:
  - lambda:UpdateFunctionConfiguration
  - s3:GetObject
  - sns:Publish
  size: large
  timeout: long
"""

from expander2.tasks import load_s3_zip

import boto3, datetime, importlib, inspect, json, os, sys, traceback, unittest

"""
- general approach to testing is to use filesystem rather than in- memory testing because latter convolves a lot of complications (is impossible?) when trying to create nested classes (notably involving module ordering) which come for free when you use the filesystem
- also because Lambda provides a nice filesystem at /tmp which mirrors what you have on dev machine
- only complication is ensuring this is cleared after each tester call to avoid mixing tests across classes;
- use `os.rm -rf` for local testing but in production need to restart container and (hopefully) get a new container with a new filesystem
"""

FileRoot="/tmp"

"""
- mainly for the benefit of local testing as production should see container restarted each time with new filesystem; but you never know
"""

def clean_filesystem(assets, root=FileRoot):
    for path in set([k.split("/")[0] for k, _, in assets]):
        # print (path)
        os.system("rm -rf %s/%s" % (root, path))
        
class SourceCode(list):

    """
    - references to __file__ are rewritten to "/tmp/#{path-to-module}" so you can split on this path, drop the trailing filename and append other static assets in the same handler directory
    """
    
    def __init__(self, items=[]):
        def rewrite_file_refs(k, v, root=FileRoot):            
            return v.replace("__file__", "\"%s/%s\"" % (FileRoot, k))
        list.__init__(self, [(k, rewrite_file_refs(k, v)) for k, v in items])

    def dump(self, root=FileRoot):
        for k, v in self:
            dirname="/".join([root]+k.split("/")[:-1])
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            filename=k.split("/")[-1]
            # print ("%s/%s" % (dirname, filename))
            with open("%s/%s" % (dirname, filename), 'w') as f:
                f.write(v)
        
class Lambdas(SourceCode):

    @classmethod
    def initialise(self, s3, bucketname, pipelineid):
        s3key="pipeline/%s/lambdas.zip" % pipelineid
        return Lambdas(load_s3_zip(s3=s3,
                                   bucketname=bucketname,
                                   key=s3key))
    
    def __init__(self, items=[]):
        SourceCode.__init__(self, items)

class Tests(SourceCode):

    @classmethod
    def initialise(self, s3, bucketname, pipelineid):
        s3key="pipeline/%s/tests.zip" % pipelineid
        return Tests(load_s3_zip(s3=s3,
                                 bucketname=bucketname,
                                 key=s3key))
    
    def __init__(self, items=[]):
        SourceCode.__init__(self, items)

    @property
    def testclasses(self):
        tests=[]
        for k, _ in self:
            modname=k.split(".")[0].replace("/", ".")
            try:
                mod=importlib.import_module(modname)
            except Exception as error:
                raise RuntimeError("%s - %s" % (modname, error))
            tests+=[obj for name, obj in inspect.getmembers(mod, inspect.isclass)
                    if name.endswith("Test")]
        return tests

    """
    - preprocessor should check that each test module has a Test class, but probably sensible to do an extra check here, just in case there is some kind of catastrophic failure with file paths that means that tests can't be found
    """
    
    def run_suite(self):
        suite=unittest.TestSuite()
        tests=self.testclasses
        if tests==[]:
            raise RuntimeError("no tests found")
        for test in tests:
            suite.addTest(unittest.makeSuite(test))
        runner=unittest.TextTestRunner()
        result=runner.run(suite)
        if (result.errors!=[] or
            result.failures!=[]):
            raise RuntimeError("/n".join([error[1]
                                          for error in result.errors+result.failures]))
    
"""
- dynamodb streaming lambda will hopefully ensure you only receive a single record at a time
- but is not impossible that more than one pipeline gets tested within a single lambda
"""
    
def handler(event, context=None,
            root=FileRoot,
            bucketname=os.environ["EXPANDER2_BUCKET"],
            topicarn=os.environ["EXPANDER2_TASKS_EVENTS_TOPIC"]):
    s3, sns, L = (boto3.client("s3"),
                  boto3.client("sns"),
                  boto3.client("lambda"))
    for record in event["detail"]["records"]:
        image={k: list(v.values())[0]
               for k, v in record["dynamodb"]["NewImage"].items()}
        """
        - because IN_PROGRESS messages could be batched by dynamodb event handler with STAGE_COMPLETE messages, event though the former are not explicitly mapped by the rule
        """
        if image["event-status"]!="STAGE_COMPLETE":
            continue
        pipelineid=image["pk"].split("#")[1]
        message=json.dumps({"pipeline": pipelineid,
                            "stage": "tester",
                            "status": "IN_PROGRESS"})
        sns.publish(TopicArn=topicarn,
                    Message=message)        
        try:
            lambdas=Lambdas.initialise(s3, bucketname, pipelineid)
            tests=Tests.initialise(s3, bucketname, pipelineid)
            clean_filesystem(lambdas+tests)
            lambdas.dump()
            tests.dump()
            if root not in sys.path:
                sys.path.insert(0, root)
            tests.run_suite()
            message=json.dumps({"pipeline": pipelineid,
                                "stage": "tester",
                                "status": "STAGE_COMPLETE"})
            sns.publish(TopicArn=topicarn,
                        Message=message)
        except RuntimeError as error:
            message=json.dumps({"pipeline": pipelineid,
                                "stage": "tester",
                                "status": "STAGE_FAILED",
                                "message": str(error)})
            sns.publish(TopicArn=topicarn,
                        Message=message)
    """
    - ALWAYS restart container to clear out whatever modules have been loaded into the interpreter as part of the testing process
    - because Lambda isn't completely stateless; containers can hang around expecting another workload; and who know what kind of module cacheing (*.pyc, __pycache__) the Python interpreter is doing inside that container
    - so force restart!
    - https://stackoverflow.com/a/60882441/124179
    """
    newdesc="lambda restarted at %s" % datetime.datetime.utcnow().isoformat()
    L.update_function_configuration(FunctionName=context.function_name,
                                    Description=newdesc)
        
