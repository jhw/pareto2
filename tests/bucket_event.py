from pareto2.dsl import DSL

from pareto2.dsl.scripts import Scripts

import unittest

IndexBody="""
\"\"\"
infra:
  events: 
  - name: whatevs
    pattern:
      foo: bar
    source:
      name: hello
      type: bucket
\"\"\"

def handler(event, context):
    pass
"""

class BucketEventTest(unittest.TestCase):

    def test_expansion(self, body=IndexBody):
        dsl=DSL()
        scripts=Scripts.initialise([("hello/index.py", body)])
        dsl.expand(scripts)
        template=dsl.spawn_template()
        template.init_implied_parameters()
        template.validate()
        rendered=template.render()
        resources=rendered["Resources"]        
        for attr in ["HelloBucket",
                     "HelloWhatevsEventRule"]:
            self.assertTrue(attr in resources)
        
if __name__=="__main__":
    unittest.main()
