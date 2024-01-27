from pareto2.dsl import DSL

from pareto2.dsl.scripts import Scripts

import unittest

IndexBody="""
\"\"\"
infra: 
  layers:
  - whatevs
\"\"\"

def handler(event, context):
    pass
"""

class SimpleLayerTest(unittest.TestCase):

    def test_expansion(self, body=IndexBody):
        dsl=DSL()
        scripts=Scripts.initialise([("hello/index.py", body)])
        dsl.expand(scripts)
        template=dsl.spawn_template()
        template.init_implied_parameters()
        template.validate()
        rendered=template.render()
        resources=rendered["Resources"]
        self.assertTrue("HelloFunction" in resources)
        self.assertTrue("Layers" in resources["HelloFunction"]["Properties"])
    
        
if __name__=="__main__":
    unittest.main()
