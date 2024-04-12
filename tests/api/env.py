from pareto2.api.env import Env

from tests.api import ApiTestBase, BucketName

from moto import mock_s3, mock_lambda, mock_acm

import boto3, os, unittest

LayerName = "whatevs"

DomainName, Region = "whatevs.com", "eu-west-1"

@mock_s3
@mock_lambda
@mock_acm
class EnvTest(ApiTestBase):

    def setUp(self):
        super().setUp()
        self.L = boto3.client("lambda")
    
    def test_environ(self):
        env = Env.create_from_environ()
        self.assertTrue("Path" in env)

    def test_bash(self):
        script = open("setenv.sh").read()
        env = Env.create_from_bash(script)
        self.assertTrue("AwsProfile" in env)

    def test_layers(self, layer_name = LayerName):
        self.L.publish_layer_version(LayerName = layer_name,
                                     Content = {"ZipFile": b''})
        env = Env()
        env.update_layers()
        self.assertTrue(env != {})

    def test_distribution_certificate(self,
                                      domain_name = DomainName,
                                      region = "us-east-1"):
        acm = boto3.client("acm", region_name = region)
        acm.request_certificate(DomainName = f"%.{domain_name}",
                                ValidationMethod = "DNS")
        env = Env({"DomainName": domain_name})
        env.update_certificates()
        self.assertTrue("DistributionCertificateArn" in env)
        self.assertTrue("RegionalCertificateArn" not in env)
        for cert in acm.list_certificates()["CertificateSummaryList"]:
            acm.delete_certificate(CertificateArn = cert["CertificateArn"])

    def test_regional_certificate(self,
                                  domain_name = DomainName,
                                  region = "eu-west-1"):
        acm = boto3.client("acm", region_name = region)
        acm.request_certificate(DomainName = f"%.{domain_name}",
                                ValidationMethod = "DNS")
        env = Env({"DomainName": domain_name,
                   "AwsRegion": region})
        env.update_certificates()
        self.assertTrue("DistributionCertificateArn" not in env)
        self.assertTrue("RegionalCertificateArn" in env)
        for cert in acm.list_certificates()["CertificateSummaryList"]:
            acm.delete_certificate(CertificateArn = cert["CertificateArn"])
        
    def tearDown(self, layer_name = LayerName):
        super().tearDown()
        for layer in self.L.list_layers()["Layers"]:
            layername=layer["LayerName"]
            version=layer["LatestMatchingVersion"]["Version"]
            self.L.delete_layer_version(LayerName=layername,
                                        VersionNumber=version)
        
if __name__ == "__main__":
    unittest.main()
