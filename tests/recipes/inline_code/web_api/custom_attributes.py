import unittest.mock as mock

from moto import mock_cognitoidp

import json, os, unittest

@mock_cognitoidp
class WebApiInlineCodeCustomAttributesTest(unittest.TestCase):

    def setUp(self):
        self.setup_cognito()
        self.env = {}
        self.env['USER_CUSTOM_ATTRIBUTES'] = json.dumps([
            {
                "name": "foo",
                "type": "str",
                "value": "bar"
            }
        ])

    def setup_cognito(self):
        pass

    def test_handler(self, event = {}):
        with mock.patch.dict(os.environ, self.env):
            from pareto2.recipes.web_api.inline_code.custom_attributes import handler
            handler(event, context = None)

    def teardown_cognito(self):
        pass
            
    def tearDown(self):
        pass
            
if __name__ == "__main__":
    unittest.main()
