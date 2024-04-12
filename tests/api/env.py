from pareto2.api.env import Env

from tests.api import ApiTestBase, BucketName

from moto import mock_s3

import os, unittest

class EnvTest(ApiTestBase):

    def setUp(self):
        super().setUp()
    
    def test_environ(self):
        env = Env.create_from_environ()
        self.assertTrue("Path" in env)

    def test_bash(self):
        script = open("setenv.sh").read()
        env = Env.create_from_bash(script)
        self.assertTrue("AwsProfile" in env)

    def test_layers(self):
        env = Env()
        env.update_layers()
        self.assertTrue(env != {})

    def test_certificates_1(self,
                            domain_name = "hello.spaas.link"):
        env = Env({"DomainName": domain_name})
        env.update_certificates()
        self.assertTrue("DistributionCertificateArn" in env)
        self.assertTrue("RegionalCertificateArn" not in env)

    def test_certificates_2(self,
                            domain_name = "hello.spaaseu.link",
                            region = "eu-west-1"):
        env = Env({"DomainName": domain_name,
                   "AwsRegion": region})
        env.update_certificates()
        self.assertTrue("DistributionCertificateArn" in env)
        self.assertTrue("RegionalCertificateArn" in env)
        
    def tearDown(self):
        super().tearDown()
       
if __name__ == "__main__":
    unittest.main()
