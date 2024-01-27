from pareto2.dsl import DSL

from pareto2.dsl.scripts import Scripts

import unittest

IndexBody="""
\"\"\"
infra:
  topic: {}
\"\"\"

def handler(event, context):
    pass
"""

class SimpleTopicTest(unittest.TestCase):

    def test_expansion(self, body=IndexBody):
        dsl=DSL()
        scripts=Scripts.initialise([("hello/index.py", body)])
        dsl.expand(scripts)
        template=dsl.spawn_template()
        template.init_implied_parameters()
        template.validate()
        rendered=template.render()
        resources=rendered["Resources"]
        for attr in ["HelloTopic"]:
            self.assertTrue(attr in resources)
        self.assertEquals(resources["HelloTopic"]["Type"], "AWS::SNS::Topic")
        
if __name__=="__main__":
    unittest.main()
