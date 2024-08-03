from tests.recipes.inline_code import EventsTestMixin

from moto import mock_cognitoidp, mock_events, mock_sqs

import unittest.mock as mock

import boto3, json, os, unittest, yaml

SampleEvent = yaml.safe_load("""
version: "1.0"
triggerSource: "PreSignUp_SignUp" # match rule
region: "us-west-2"
userPoolId: "us-west-2_aaaaaaaaa" # overwritten by test case
userName: "foo@bar.com"
callerContext:
  awsSdkVersion: "aws-sdk-unknown-unknown"
  clientId: "1example23456789"
request:
  userAttributes:
    sub: "12345678-1234-1234-1234-123456789012"
    email_verified: "true"
    email: "something@different.com"
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

PoolName, Username = "hello-pool", "foo@bar.com"

@mock_events
@mock_sqs
@mock_cognitoidp
class CustomAttributesInlineCodeTest(unittest.TestCase,
                                     EventsTestMixin):

    def setUp(self, rules = Rules):
        self.setup_events(rules = Rules)
        self.setup_cognito()
        self.env = {}
        self.env['USER_CUSTOM_ATTRIBUTES'] = json.dumps([
            {
                "name": "foo",
                "value": "bar"
            }
        ])

    def setup_cognito(self, pool_name = PoolName, username = Username):
        self.cognito = boto3.client("cognito-idp")
        response = self.cognito.create_user_pool(
            PoolName = pool_name,
            Schema=[
                {
                    'Name': 'email',
                    'AttributeDataType': 'String',
                    'Mutable': True,
                    'Required': True,
                },
                {
                    'Name': 'custom:foo',
                    'AttributeDataType': 'String',
                    'Mutable': True
                }
            ]
        )
        self.user_pool_id = response['UserPool']['Id']
        self.cognito.admin_create_user(
            UserPoolId = self.user_pool_id,
            Username = username,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': username
                }
            ],
            MessageAction='SUPPRESS'
        )

    def test_handler(self,
                     event = SampleEvent,
                     username = Username):
        event = dict(event)
        event["userPoolId"] = self.user_pool_id # else handler can't find pool
        with mock.patch.dict(os.environ, self.env):
            from pareto2.recipes.web_api.inline_code.custom_attributes import handler
            event_ = handler(event, context = None)
            self.assertTrue("version" in event_) # assert JSON returned
            # user attributes
            user = self.cognito.admin_get_user(
                UserPoolId = self.user_pool_id,
                Username = username
            )
            attributes = {attr["Name"]:attr["Value"]
                          for attr in user["UserAttributes"]}
            self.assertTrue("custom:foo" in attributes)
            self.assertEqual(attributes["custom:foo"], "bar")
            # message push
            messages = self.drain_queue(queue = self.events_queue)
            self.assertTrue(len(messages) == 1)
            message = messages.pop()
            body = json.loads(message["Body"])
            self.assertTrue("detail" in body)
            
    def teardown_cognito(self, username = Username):
        self.cognito.admin_delete_user(
            UserPoolId = self.user_pool_id,
            Username = username
        )
        self.cognito.delete_user_pool(
            UserPoolId = self.user_pool_id
        )
            
    def tearDown(self):
        self.teardown_cognito()
        self.teardown_events()
            
if __name__ == "__main__":
    unittest.main()
