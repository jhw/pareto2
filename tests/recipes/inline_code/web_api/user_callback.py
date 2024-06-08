from tests.recipes.inline_code import EventsTestMixin

from moto import mock_events, mock_sqs

import unittest.mock as mock

import json, os, unittest, yaml

SampleEvent = yaml.safe_load("""
version: "1.0"
triggerSource: "PreSignUp_SignUp"
region: "us-west-2"
userPoolId: "us-west-2_aaaaaaaaa"
userName: "janedoe"
callerContext:
  awsSdkVersion: "aws-sdk-unknown-unknown"
  clientId: "1example23456789"
request:
  userAttributes:
    sub: "12345678-1234-1234-1234-123456789012"
    email_verified: "true"
    email: "janedoe@example.com"
  validationData:
    someKey: "someValue"
response:
  autoConfirmUser: false
  autoVerifyEmail: false
  autoVerifyPhone: false
""")

Rules = yaml.safe_load("""
- detail:
    triggerSource: 
    - PreSignUp_SignUp
""")

@mock_events
@mock_sqs
class WebApiInlineUserCallbackTest(unittest.TestCase,
                                       EventsTestMixin):

    def setUp(self, rules = Rules):        
        self.env = {}
        self.env["APP_USER_POOL"] = "app-user-pol" # doesn't have to be mocked, is passed as source reference only
        self.setup_events(rules = rules)
    
    def test_code(self, event = SampleEvent):
        with mock.patch.dict(os.environ, self.env):
            from pareto2.recipes.web_api.inline_code.user_callback import handler
            handler(event, context = None)
            messages = self.drain_queue(queue = self.events_queue)
            self.assertTrue(len(messages) == 1)
            message = messages.pop()
            body = json.loads(message["Body"])
            self.assertTrue("detail" in body)

    def tearDown(self):
        self.teardown_events()
            
if __name__ == "__main__":
    unittest.main()
