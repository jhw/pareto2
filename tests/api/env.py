"""
Env is tested against real AWS resources rather than mock as is read- only
"""

from pareto2.api.env import Env

import os, unittest

class EnvTest(unittest.TestCase):
    
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

    """
    as of 12/04/24 spaas.link has us-east-1 certificate only
    """
        
    def test_certificates_1(self,
                            domain_name = "hello.spaas.link"):
        env = Env({"DomainName": domain_name})
        env.update_certificates()
        self.assertTrue("DistributionCertificateArn" in env)
        self.assertTrue("RegionalCertificateArn" not in env)

    """
    as of 12/04/24 spaaseu.link has both us-east-1 and eu-west-1 certificates
    """
        
    def test_certificates_2(self,
                            domain_name = "hello.spaaseu.link",
                            region = "eu-west-1"):
        env = Env({"DomainName": domain_name,
                   "AwsRegion": region})
        env.update_certificates()
        self.assertTrue("DistributionCertificateArn" in env)
        self.assertTrue("RegionalCertificateArn" in env)
        
if __name__ == "__main__":
    unittest.main()
