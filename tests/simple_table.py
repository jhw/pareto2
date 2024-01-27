from pareto2.dsl import DSL

from pareto2.dsl.scripts import Scripts

import unittest

IndexBody="""
\"\"\"
infra: {}
\"\"\"

import os

def handler(event, context):
    tablename=os.environ["HELLO_TABLE"]
"""

class SimpleTableTest(unittest.TestCase):

    def test_expansion(self, body=IndexBody):
        dsl=DSL()
        scripts=Scripts.initialise([("hello/index.py", body)])
        dsl.expand(scripts)
        template=dsl.spawn_template()
        template.init_implied_parameters()
        template.validate()
        rendered=template.render()
        resources=rendered["Resources"]
        for attr in ["HelloTable",
                     "HelloTableStreamingFunction"]:
            self.assertTrue(attr in resources)
        self.assertEqual(resources["HelloTable"]["Type"], "AWS::DynamoDB::Table")
        

if __name__=="__main__":
    unittest.main()
