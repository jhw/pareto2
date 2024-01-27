from pareto2.dsl import DSL

from pareto2.dsl.scripts import Scripts

import unittest

IndexBody="""
\"\"\"
infra: {}
\"\"\"

import os

def handler(event, context):
    bucketname=os.environ["HELLO_WEBSITE"]
"""

class SimpleWebsiteTest(unittest.TestCase):

    def test_expansion(self, body=IndexBody):
        dsl=DSL()
        scripts=Scripts.initialise([("hello/index.py", body)])
        dsl.expand(scripts)
        template=dsl.spawn_template()
        template.init_implied_parameters()
        template.validate()
        rendered=template.render()
        resources=rendered["Resources"]
        for attr in ["HelloWebsite",
                     "HelloWebsiteRestApi"]:
            self.assertTrue(attr in resources)
        self.assertEqual(resources["HelloWebsite"]["Type"], "AWS::S3::Bucket")
        self.assertTrue("HelloBucket" not in resources)
        
if __name__=="__main__":
    unittest.main()
