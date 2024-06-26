import unittest.mock as mock

import json, os, unittest

class WebApiInlineCodeCustomAttributesTest(unittest.TestCase):

    def setUp(self):        
        self.env = {}
        self.env['USER_CUSTOM_ATTRIBUTES'] = json.dumps([
            {
                "name": "foo",
                "type": "str",
                "value": "bar"
            }
        ])

    def test_handler(self, event = {}):
        with mock.patch.dict(os.environ, self.env):
            from pareto2.recipes.web_api.inline_code.custom_attributes import handler
            handler(event, context = None)

    def tearDown(self):
        pass
            
if __name__ == "__main__":
    unittest.main()
