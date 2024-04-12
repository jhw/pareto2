"""
Env is tested against real AWS resources rather than mock as is read- only
"""

from pareto2.api.env import Env

import boto3, os, unittest

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
        env.update_layers(boto3.client("lambda"))
        self.assertTrue(env != {})

if __name__ == "__main__":
    unittest.main()
