import unittest.mock as mock

from moto import mock_cognitoidp

import boto3, json, os, unittest, yaml

SampleEvent = yaml.safe_load("""
version: "1.0"
triggerSource: "whatevs_man" 
region: "us-west-2"
userPoolId: "us-west-2_aaaaaaaaa" # overwritten by test case
userName: "janedoe"
callerContext:
  awsSdkVersion: "aws-sdk-unknown-unknown"
  clientId: "1example23456789"
request:
  userAttributes:
    sub: "12345678-1234-1234-1234-123456789012"
    email_verified: "true"
    email: "foo@bar.com" # consistent with Username
  validationData:
    someKey: "someValue"
response:
  autoConfirmUser: false
  autoVerifyEmail: false
  autoVerifyPhone: false
""")

PoolName, Username = "hello-pool", "foo@bar.com"

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

    def test_handler(self, event = SampleEvent):
        event = dict(event)
        event["userPoolId"] = self.user_pool_id # else handler can't find pool
        with mock.patch.dict(os.environ, self.env):
            from pareto2.recipes.web_api.inline_code.custom_attributes import handler
            handler(event, context = None)

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
            
if __name__ == "__main__":
    unittest.main()
