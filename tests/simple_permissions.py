from pareto2.dsl import DSL

from pareto2.dsl.scripts import Scripts

import unittest

IndexBody="""
\"\"\"
infra: 
  permissions:
  - foo:bar
\"\"\"

def handler(event, context):
    pass
"""

class SimplePermissionsTest(unittest.TestCase):

    def test_expansion(self, body=IndexBody):
        dsl=DSL()
        scripts=Scripts.initialise([("hello/index.py", body)])
        dsl.expand(scripts)
        template=dsl.spawn_template()
        template.init_implied_parameters()
        template.validate()
        rendered=template.render()
        resources=rendered["Resources"]
        self.assertTrue("HelloFunctionRole" in resources)
        roleprops=resources["HelloFunctionRole"]["Properties"]
        self.assertTrue("Policies" in roleprops)
        policy=roleprops["Policies"].pop()
        self.assertTrue("PolicyDocument" in policy)
        policydoc=policy["PolicyDocument"]
        self.assertTrue("Statement" in policydoc)
        actions=[]
        for item in policydoc["Statement"]:
            actions+=item["Action"]
        self.assertTrue("foo:bar" in actions)
        
if __name__=="__main__":
    unittest.main()
