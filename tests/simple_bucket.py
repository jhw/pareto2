from pareto2.dsl import DSL

from pareto2.dsl.scripts import Scripts

import unittest

IndexBody="""
\"\"\"
infra: {}
\"\"\"

import os

def handler(event, context):
    bucketname=os.environ["HELLO_BUCKET"]
"""

class SimpleBucketTest(unittest.TestCase):

    def test_expansion(self, body=IndexBody):
        dsl=DSL()
        scripts=Scripts.initialise([("hello/index.py", body)])
        dsl.expand(scripts)
        template=dsl.spawn_template()
        template.init_implied_parameters()
        template.validate()
        rendered=template.render()
        resources=rendered["Resources"]        
        self.assertTrue("HelloBucket" in resources)
        self.assertEquals(resources["HelloBucket"]["Type"], "AWS::S3::Bucket")
        self.assertTrue("HelloWebsite" not in resources)
        
if __name__=="__main__":
    unittest.main()
