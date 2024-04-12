from pareto2.services import hungarorise as H

import os

class Env(dict):

    @classmethod
    def create_from_environ(self):
        return Env({H(k):v for k, v in os.environ.items()})

    @classmethod
    def create_from_bash(self, text):
        def init_tuple(kv):
            return (H(kv[0]), kv[1])
        cleantext="\n".join([" ".join([tok for tok in row.split(" ")
                                       if tok != ''])
                             for row in text.split("/n")
                             if row != []])
        return Env(dict([init_tuple([tok.replace('"', "")
                                     for tok in row.split(" ")[1].split("=")])
                         for row in text.split("\n")
                         if row.startswith("export")]))
    
    def __init__(self, item = {}):
        dict.__init__(self, item)

    def update_layers(self, L):
        resp=L.list_layers()
        if "Layers" in resp:
            self.update({H("%s-layer-arn" % layer["LayerName"]):layer["LatestMatchingVersion"]["LayerVersionArn"]
                         for layer in resp["Layers"]})

    @property
    def has_domain_name(self):
        return "DomainName" in self

    @property
    def domain_name(self):
        return ".".join(self["DomainName"].split(".")[1:])

    @property
    def has_aws_region(self):
        return "AwsRegion" in self
    
    """
    acm doesn't seem to have the ability to filter by domain name
    """
    
    def list_certificates(self, acm, domain_name):
        resp, certificates = acm.list_certificates(), {}
        if "CertificateSummaryList" in resp:
            for cert in resp["CertificateSummaryList"]:
                if domain_name in cert["DomainName"]:
                    certificate_arn = cert["CertificateArn"]
                    region = certificate_arn.split(":")[3]
                    certificates.setdefault(region, [])                    
                    certificates[region].append(certificate_arn)
        return certificates

    def update_distribution_certificate(self, certificates, region = "us-east-1"):
        if region in certificates:
            self["DistributionCertificateArn"] = certificates[region][0]

    def update_regional_certificate(self, certificates):        
        if self.has_aws_region:
            region = self["AwsRegion"]
            if region in certificates:
                self["RegionalCertificateArn"] = certificates[region][0]
            
    def update_certificates(self, acm):
        if self.has_domain_name:
            certificates = self.list_certificates(acm, self.domain_name)
            self.update_distribution_certificate(certificates)
            self.update_regional_certificate(certificates)

if __name__ == "__main__":
    pass
