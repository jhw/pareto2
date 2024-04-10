from pareto.api import file_loader, build_stack

import boto3, io, os, re, zipfile

from datetime import datetime

def FilterFn(file_name):
    return not (file_name.endswith(".pyc") or
                file_name.endswith("test.py"))

def hungarorise(text):
    return "".join([tok.lower().capitalize()
                    for tok in re.split("\\-|\\_", text)
                    if tok != ''])

class Lambdas(dict):

    def __init__(self, assets = {}):
        dict.__init__(self, assets)

    """
    - https://chat.openai.com/c/34736a67-aa28-4662-ad65-1c2d522e67ec
    """
        
    @property
    def zip_buffer(self):
        buf = io.BytesIO()
        zf = zipfile.ZipFile(buf, "a", zipfile.ZIP_DEFLATED, False)
        for k, v in self.items():
            # zf.writestr(k, v)
            unix_mode = 0o100644  # File permission: rw-r--r--
            zip_info = zipfile.ZipInfo(k)
            zip_info.external_attr = (unix_mode << 16) | 0o755  # Add execute permission
            zf.writestr(zip_info, v)
        zf.close()
        return buf.getvalue()

    def put_s3(self, s3, bucket_name, file_name):
        s3.put_object(Bucket = bucket_name,
                      Key = file_name,
                      Body = self.zip_buffer,
                      ContentType = "application/gzip")

class Env(dict):

    def __init__(self, L, acm):
        dict.__init__(self, {hungarorise(k):v
                             for k, v in os.environ.items()})
        for attr in ["AppName", "ArtifactsBucket", "AWSRegion"]:
            if attr not in self:
                raise RuntimeError(f"env is missing {attr}")
        self.update(self.list_layers(L))
        if "DomainName" in self:
            self.insert_certificate(acm)

    def list_layers(self, L):
        resp = L.list_layers()
        return {hungarorise("%s-layer-arn" % layer["LayerName"]):layer["LatestMatchingVersion"]["LayerVersionArn"]
                for layer in resp["Layers"]} if "Layers" in resp else {}

    def insert_certificate(self, acm):
        domainname = ".".join(self["DomainName"].split(".")[1:])
        resp = acm.list_certificates()
        certs = {".".join(cert["DomainName"].split(".")[1:]):cert["CertificateArn"]
               for cert in resp["CertificateSummaryList"]} if "CertificateSummaryList" in resp else {}
        if domainname not in certs:
            raise RuntimeError("no certificate found for %s" % domainname)
        self["CertificateArn"] = certs[domainname]
    
class Assets:

    def __init__(self, env, s3, filter_fn = FilterFn):
        self.env = env
        self.s3 = s3
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        self.lambdas = Lambdas({path: content
                                for path, content in file_loader(pkg_root = self.env.AppName,
                                                                 filter_fn = filter_fn)})

    def put_template(self):
        recipe = build_stack(self.lambdas)
        template = recipe.render()
        template.populate_parameters()
        for file_slug in [self.timestamp,
                          "latest"]:
            template.dump_s3(s3 = self.s3,
                             bucket_name = self.env.BucketName,
                             file_name = f"template/{file_slug}.json")

    def put_lambdas(self):
        self.lambdas.put_s3(s3 = self.s3,
                            bucket_name = self.env.BucketName,
                            file_name = f"lambdas/{self.timestamp}.zip")

if __name__ == "__main__":
    try:
        L, acm = (boto3.client("lambda"),
                  boto3.client("acm", region_name = "us-east-1"))
        env = Env(L, acm)
        s3 = boto3.client("s3")
        assets = Assets(env, s3)
        assets.put_template()
        assets.put_lambdas()
    except RuntimeError as error:
        print ("Error: %s" % str(error))

