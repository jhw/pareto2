import boto3, io, os, re, zipfile

from datetime import datetime

def FilterFn(file_name):
    return not (file_name.endswith(".pyc") or
                file_name.endswith("test.py"))

def hungarorise(text):
    return "".join([tok.lower().capitalize()
                    for tok in re.split("\\-|\\_", text)
                    if tok != ''])

class Lambdas(list):

    @classmethod
    def initialise(self, app_name, timestamp, filterfn = FilterFn):
        root, assets = app_name.replace("-", ""), []
        for localroot, _, files in os.walk(root):
            for file_name in files:
                if filterfn(file_name):
                    abs_file_name = os.path.join(localroot, file_name)
                    key = "/".join(abs_file_name.split("/"))
                    assets.append((key, open(abs_file_name).read()))
        return Lambdas(app_name, timestamp, assets)
                       
    def __init__(self, app_name, timestamp, items):
        list.__init__(self, items)
        self.app_name = app_name
        self.timestamp = timestamp

    """
    - https://chat.openai.com/c/34736a67-aa28-4662-ad65-1c2d522e67ec
    """
        
    @property
    def zip_buffer(self):
        buf = io.BytesIO()
        zf = zipfile.ZipFile(buf, "a", zipfile.ZIP_DEFLATED, False)
        for k, v in self:
            # zf.writestr(k, v)
            unix_mode = 0o100644  # File permission: rw-r--r--
            zip_info = zipfile.ZipInfo(k)
            zip_info.external_attr = (unix_mode << 16) | 0o755  # Add execute permission
            zf.writestr(zip_info, v)
        zf.close()
        return buf.getvalue()

    @property
    def s3_key(self):
        return "lambdas-%s.zip" % self.timestamp
    
    def put_s3(self, s3, bucket_name):
        s3.put_object(Bucket = bucket_name,
                      Key = self.s3_key,
                      Body = self.zip_buffer,
                      ContentType = "application/gzip")

class Env(dict):

    def __init__(self, L, acm):
        dict.__init__(self, {hungarorise(k):v
                             for k, v in os.environ.items()})
        for attr in ["AppName", "ArtifactsBucket"]:
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

    def __init__(self, env, s3):
        self.env = env
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        self.lambdas = Lambdas.initialise(self.env.AppName, self.timestamp)

    def put_template(self):
        pass

    def put_lambdas(self):
        self.lambdas.put_s3(self.s3, self.env.BucketName)

if __name__ == "__main__":
    try:
        s3, L, acm = (boto3.client("s3"),
                      boto3.client("lambda"),
                      boto3.client("acm", region_name = "us-east-1"))
        env = Env(L, acm)
        assets = Assets(env)
        assets.put_template(s3)
        assets.put_lambdas(s3)
    except RuntimeError as error:
        print ("Error: %s" % str(error))

