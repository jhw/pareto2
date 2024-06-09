import unittest.mock as mock

import json, os, unittest, yaml

AdminCreateUserEvent = yaml.safe_load("""
triggerSource: "CustomMessage_AdminCreateUser"
region: "us-east-1"
userPoolId: "us-east-1_123456789"
userName: "user@example.com"
callerContext:
  awsSdkVersion: "aws-sdk-unknown-unknown"
  clientId: "abcd1234abcd1234abcd1234"
request:
  userAttributes:
    sub: "12345678-1234-1234-1234-123456789012"
    email_verified: "true"
    email: "user@example.com"
    given_name: "John"
    family_name: "Doe"
  codeParameter: "TEMP_PASSWORD_1234"
  linkParameter: ""
  usernameParameter: ""
response:
  smsMessage: ""
  emailMessage: ""
  emailSubject: ""
  smsSubject: ""
""")

ForgotPasswordEvent = yaml.safe_load("""
triggerSource: "CustomMessage_ForgotPassword"
region: "us-east-1"
userPoolId: "us-east-1_123456789"
userName: "user@example.com"
callerContext:
  awsSdkVersion: "aws-sdk-unknown-unknown"
  clientId: "abcd1234abcd1234abcd1234"
request:
  userAttributes:
    sub: "12345678-1234-1234-1234-123456789012"
    email_verified: "true"
    email: "user@example.com"
    given_name: "John"
    family_name: "Doe"
  codeParameter: "RESET_CODE_5678"
  linkParameter: ""
  usernameParameter: ""
response:
  smsMessage: ""
  emailMessage: ""
  emailSubject: ""
  smsSubject: ""
""")

class WebApiInlineCodeCustomMessageTest(unittest.TestCase):

    def setUp(self):        
        self.env = {}
        self.env['TEMP_PASSWORD_EMAIL_SUBJECT'] = 'Temporary Password'
        self.env['TEMP_PASSWORD_EMAIL_MESSAGE'] = 'Your temporary password is {codeParameter}'
        self.env['PASSWORD_RESET_EMAIL_SUBJECT'] = 'Password Reset'
        self.env['PASSWORD_RESET_EMAIL_MESSAGE'] = 'Your password reset code is {codeParameter}'
    
    def test_admin_create_user(self, event = AdminCreateUserEvent):
        with mock.patch.dict(os.environ, self.env):
            from pareto2.recipes.web_api.inline_code.custom_message import handler
            modevent = handler(event, context = None)
            response = modevent["response"]
            self.assertTrue("emailSubject" in response)
            self.assertEqual(response["emailSubject"], 'Temporary Password')
            self.assertTrue("emailMessage" in response)
            self.assertEqual(response["emailMessage"], 'Your temporary password is TEMP_PASSWORD_1234')

    def test_forgot_password(self, event = ForgotPasswordEvent):
        with mock.patch.dict(os.environ, self.env):
            from pareto2.recipes.web_api.inline_code.custom_message import handler
            modevent = handler(event, context = None)
            response = modevent["response"]
            self.assertTrue("emailSubject" in response)
            self.assertEqual(response["emailSubject"], 'Password Reset')
            self.assertTrue("emailMessage" in response)
            self.assertEqual(response["emailMessage"], 'Your password reset code is RESET_CODE_5678')


    def tearDown(self):
        pass
            
if __name__ == "__main__":
    unittest.main()