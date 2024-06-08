import unittest.mock as mock

import base64, gzip, json, os, unittest

SampleEvent = {
    "awslogs":{
        "data": base64.b64encode(gzip.compress(json.dumps({"hello": "world"}).encode("utf-8")))
    }
}

class SlackInlineCodeTest(unittest.TestCase):

    def setUp(self):        
        self.env = {}
        # self.env["SLACK_WEBHOOK_URL"] = "https://httpbin.org/post"
        self.env["SLACK_WEBHOOK_URL"] = "http://news.bbc.co.uk"
        self.env["SLACK_LOGGING_LEVEL"] = "info"

    def test_alerts(self, event = SampleEvent):
        with mock.patch.dict(os.environ, self.env):
            from pareto2.recipes.mixins.alerts.inline_code import handler
            handler(event, context = None)

    def test_alarms(self, event = SampleEvent):
        with mock.patch.dict(os.environ, self.env):
            from pareto2.recipes.mixins.alarms.inline_code import handler
            handler(event, context = None)

    def tearDown(self):
        pass
            
if __name__ == "__main__":
    unittest.main()
