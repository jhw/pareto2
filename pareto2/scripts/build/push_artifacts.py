from pareto2.config.scripts import Scripts

from pareto2.config import Config, ComponentModules

import boto3, io, json, os, re, zipfile

from datetime import datetime

def FilterFn(filename):
    return not (filename.endswith(".pyc") or
                filename.endswith("test.py"))

def hungarorise(text):
    return "".join([tok.lower().capitalize()
                    for tok in re.split("\\-|\\_", text)
                    if tok!=''])

class Lambdas(list):

    @classmethod
    def initialise(self, appname, timestamp, filterfn=FilterFn):
        root, assets = appname.replace("-", ""), []
        for localroot, _, files in os.walk(root):
            for filename in files:
                if filterfn(filename):
                    absfilename=os.path.join(localroot, filename)
                    key="/".join(absfilename.split("/"))
                    assets.append((key, open(absfilename).read()))
        return Lambdas(appname, timestamp, assets)
                       
    def __init__(self, appname, timestamp, items):
        list.__init__(self, items)
        self.appname=appname
        self.timestamp=timestamp

    @property
    def zip_buffer(self):
        buf=io.BytesIO()
        zf=zipfile.ZipFile(buf, "a", zipfile.ZIP_DEFLATED, False)
        for k, v in self:
            zf.writestr(k, v)
        zf.close()
        return buf.getvalue()

    @property
    def s3_key(self):
        return "lambdas-%s.zip" % self.timestamp
    
    def put_s3(self, s3, bucketname):
        s3.put_object(Bucket=bucketname,
                      Key=self.s3_key,
                      Body=self.zip_buffer,
                      ContentType="application/gzip")

"""
- wrapper class which allows you to remove s3- related code within Template, which shouldn't really exist
- need to check for any pareto2 code which explicitly uses boto3 code, excepting test stuff
"""
        
class TemplateWrapper:

    def __init__(self, appname, timestamp, template):
        self.appname=appname
        self.timestamp=timestamp
        self.template=template

    def to_json(self):
        return json.dumps(self.template.render(),
                          indent=2)

    @property
    def s3_timestamped_key(self):
        return "template-%s.json" % self.timestamp

    @property
    def s3_latest_key(self):
        return "template-latest.json"

    def rewrite_dash_names(self):
        for resource in self.template.resources.values():
            if resource["Type"]=="AWS::CloudWatch::Dashboard":                
                props=resource["Properties"]
                modname="%s-%s" % (self.appname, props["DashboardName"])
                props["DashboardName"]=modname
        return self
    
    def put_s3(self, s3, bucketname):
        for s3key in [self.s3_timestamped_key,
                      self.s3_latest_key]:
            s3.put_object(Bucket=bucketname,
                          Key=s3key,
                          Body=self.to_json(),
                          ContentType="application/json")

class Assets:

    def __init__(self, appname):
        self.appname=appname
        self.timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        self.lambdas=Lambdas.initialise(self.appname, self.timestamp)
        
    def spawn_config(self):
        config=Config()
        indexfiles=[(filename, body)
                    for filename, body in self.lambdas
                    if filename.endswith("index.py")]
        scripts=Scripts.initialise(indexfiles)
        config.expand(scripts)
        self.config=config

    def lookup_env_variables(self, suffixes=["_API_KEY",
                                             "_ARN",
                                             "DOMAIN_NAME", # NB no underscore prefix
                                             "_DOMAIN_PREFIX",
                                             "_WEBHOOK"]):
        variables={}
        for key, value in os.environ.items():
            for suffix in suffixes:
                if key.endswith(suffix):
                    variables[hungarorise(key)]=value
        return variables
        
    def put_template(self, s3, modules=ComponentModules):
        template=self.config.spawn_template(modules)
        template.init_implied_parameters()
        parameters=self.config.parameters
        parameters["ArtifactsBucket"]=os.environ["ARTIFACTS_BUCKET"]
        parameters["ArtifactsKey"]=self.lambdas.s3_key
        parameters.update(self.lookup_env_variables())
        template.parameters.update_defaults(parameters)
        template.parameters.validate()
        template.validate()
        TemplateWrapper(self.appname, self.timestamp, template).rewrite_dash_names().put_s3(s3, os.environ["ARTIFACTS_BUCKET"])

    def put_lambdas(self, s3):
        self.lambdas.put_s3(s3, os.environ["ARTIFACTS_BUCKET"])

if __name__=="__main__":
    try:
        appname=os.environ["APP_NAME"]
        if appname in ["", None]:
            raise RuntimeError("APP_NAME does not exist")
        assets=Assets(appname)
        s3=boto3.client("s3")
        assets.spawn_config()
        assets.put_template(s3)
        assets.put_lambdas(s3)
    except RuntimeError as error:
        print ("Error: %s" % str(error))

