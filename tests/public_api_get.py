from pareto2.dsl import DSL

from pareto2.dsl.scripts import Scripts

import unittest

IndexBody="""
\"\"\"
infra:
  endpoint: 
    api: public
    path: echo
    method: GET
    parameters:
    - message
\"\"\"

def handler(event, context):
    print (event)
"""

class PublicApiGetTest(unittest.TestCase):

    def test_expansion(self, body=IndexBody):
        dsl=DSL()
        scripts=Scripts.initialise([("hello/index.py", body)])
        dsl.expand(scripts)
        template=dsl.spawn_template()
        template.init_implied_parameters()
        template.validate()
        rendered=template.render()
        resources=rendered["Resources"]
        for attr in["WarnLogsFunction",
                    "ErrorLogsFunction",
                    "HelloFunction",
                    "HelloWarnLogsSubscription",
                    "HelloErrorLogsSubscription",
                    "PublicApiDomain",
                    "PublicApiRestApi",
                    "EchoApiResource",
                    "EchoApiValidator",
                    "EchoApiCorsMethod"]:
            self.assertTrue(attr in resources)
            validatorprops=resources["EchoApiValidator"]["Properties"]
        self.assertTrue("ValidateRequestParameters" in validatorprops and
                        validatorprops["ValidateRequestParameters"] and
                        "ValidateRequestBody" not in validatorprops)
        for attr in ["HelloTable",
                     "HelloBucket",
                     "HelloWebsite",
                     "PublicApiUserpool",
                     "EchoApiModel"]:
            self.assertFalse(attr in resources)

if __name__=="__main__":
    unittest.main()
