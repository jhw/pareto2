from pareto2.dsl import DSL

from pareto2.dsl.scripts import Scripts

import unittest

IndexBody="""
\"\"\"
infra:
  timer:
    rate: "1 hour"
    body:
      hello: world
\"\"\"

def handler(event, context):
    pass
"""

class SimpleTimerTest(unittest.TestCase):

    def test_expansion(self, body=IndexBody):
        dsl=DSL()
        scripts=Scripts.initialise([("hello/index.py", body)])
        dsl.expand(scripts)
        template=dsl.spawn_template()
        template.init_implied_parameters()
        template.validate()
        rendered=template.render()
        resources=rendered["Resources"]
        for attr in ["HelloTimer"]:
            self.assertTrue(attr in resources)
        self.assertEqual(resources["HelloTimer"]["Type"], "AWS::Events::Rule")
        
if __name__=="__main__":
    unittest.main()
