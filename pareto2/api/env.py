from pareto2.services import hungarorise as H

import boto3
import json
import os
import re

class Env(dict):

    @classmethod
    def create_from_environ(self):
        return Env({H(k):v for k, v in os.environ.items()})

    @classmethod
    def create_from_bash(self, text):
        def extract_exports(bash_script):
            export_pattern = re.compile(r'export (\w+)=["\']?([^"\']*)["\']?')
            exports = {}            
            for line in bash_script.splitlines():
                match = export_pattern.match(line.strip())
                if match:
                    key, value = match.groups()
                    exports[key] = value
            return exports
        return Env({H(k):v for k, v in extract_exports(text).items()})
    
    def __init__(self, item = {}):
        dict.__init__(self, item)

    def validate(self):
        for attr in ["AppName",
                     "PkgRoot",
                     "SlackWebhookUrl"]:
            if attr not in self:
                raise RuntimeError(f"env is missing {attr}")
        if "DomainName" in self:          
            if len(self["DomainName"].split(".")) != 3:
                raise RuntimeError("DOMAIN_NAME must be fully qualified")
            if "AwsRegion" not in self:
                raise RuntimeError("AWS_REGION must be defined if DOMAIN_NAME is defined")

    def update_layers(self):
        resp=boto3.client("lambda").list_layers()
        if "Layers" in resp:
            self.update({H("%s-layer-arn" % layer["LayerName"]):layer["LatestMatchingVersion"]["LayerVersionArn"]
                         for layer in resp["Layers"]})

    @property
    def has_domain_name(self):
        return "DomainName" in self

    @property
    def domain_name(self):
        return ".".join(self["DomainName"].split(".")[-2:])

    """
    acm requires you to create a client on a per region basis
    """
    
    def list_certificates(self, regions, domain_name):
        certificates = {}
        for region in regions:
            acm = boto3.client("acm", region_name = region)
            resp = acm.list_certificates()
            if "CertificateSummaryList" in resp:
                for cert in resp["CertificateSummaryList"]:
                    if domain_name in cert["DomainName"]:
                        certificate_arn = cert["CertificateArn"]
                        certificates.setdefault(region, [])                    
                        certificates[region].append(certificate_arn)
        return certificates

    def update_distribution_certificate(self, certificates, region = "us-east-1"):
        if region in certificates:
            self["DistributionCertificateArn"] = certificates[region][0]

    @property
    def has_aws_region(self):
        return "AwsRegion" in self
            
    def update_regional_certificate(self, certificates):        
        if self.has_aws_region:
            region = self["AwsRegion"]
            if region in certificates:
                self["RegionalCertificateArn"] = certificates[region][0]
            
    def update_certificates(self):
        regions = {"us-east-1"}
        if self.has_aws_region:
            if self["AwsRegion"] not in regions:                
                regions.add(self["AwsRegion"])
        if self.has_domain_name:
            certificates = self.list_certificates(regions, self.domain_name)
            self.update_distribution_certificate(certificates)
            self.update_regional_certificate(certificates)

    def dump_s3(self, s3, bucket_name, key):
        s3.put_object(Bucket = bucket_name,
                      Key = key,
                      Body = json.dumps(self,
                                        indent = 2),
                      ContentType = "application/json")
            
if __name__ == "__main__":
    pass
