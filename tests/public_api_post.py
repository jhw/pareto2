from pareto2.dsl import DSL

from pareto2.dsl.scripts import Scripts

import unittest

IndexBody="""
\"\"\"
infra:
  endpoint: 
    api: public
    path: upload
    method: POST
    schema: {}
\"\"\"

def handler(event, context):
    print (event)
"""

class PublicApiPostTest(unittest.TestCase):

    def test_expansion(self, body=IndexBody):
        dsl=DSL()
        scripts=Scripts.initialise([("hello/index.py", body)])
        dsl.expand(scripts)
        template=dsl.spawn_template()
        template.init_implied_parameters()
        template.validate()
        rendered=template.render()
        resources=rendered["Resources"]
        for attr in ["WarnLogsFunction",
                     "ErrorLogsFunction",
                     "HelloFunction",
                     "HelloWarnLogsSubscription",
                     "HelloErrorLogsSubscription",
                     "PublicApiDomain",
                     "PublicApiRestApi",
                     "UploadApiResource",
                     "UploadApiValidator",
                     "UploadApiModel",
                     "UploadApiCorsMethod"]:
            self.assertTrue(attr in resources)
        validatorprops=resources["UploadApiValidator"]["Properties"]
        self.assertTrue("ValidateRequestBody" in validatorprops and
                        validatorprops["ValidateRequestBody"] and
                        "ValidateRequestParameters" not in validatorprops)
        for attr in ["HelloTable",
                     "HelloBucket",
                     "HelloWebsite",
                     "PublicApiUserpool"]:
            self.assertFalse(attr in resources)
        
if __name__=="__main__":
    unittest.main()
