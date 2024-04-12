"""
Env is tested against real AWS resources rather than mock as is read- only
"""

from pareto2.api.env import Env

import os, unittest

DomainName, Region = "spaas.link", "eu-west-1"

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

    def test_certificates(self,
                          domain_name = DomainName,
                          region = Region):
        env = Env({"DomainName": domain_name,
                   "AwsRegion": region})
        env.update_certificates()
        for attr in ["DistributionCertificateArn",
                     "RegionalCertificateArn"]:
            self.assertTrue(attr in env)
        
if __name__ == "__main__":
    unittest.main()
