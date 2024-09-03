import unittest.mock as mock

import json, os, unittest, yaml

AdminCreateUserEvent = yaml.safe_load("""
triggerSource: "CustomMessage_AdminCreateUser"
region: "us-east-1"
userPoolId: "us-east-1_123456789"
userName: "ABC-DEF"
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
  codeParameter: "{####}" # NB ** THIS VALUE IS MANDATED BY COGNITO **
  linkParameter: "{##Click Here##}" # NB ** THIS VALUE IS MANDATED BY COGNITO **
  usernameParameter: "{username}" # NB ** THIS VALUE IS MANDATED BY COGNITO **
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
userName: "ABD-DEF"
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
  codeParameter: "{####}"
  linkParameter: ""
  usernameParameter: ""
response:
  smsMessage: ""
  emailMessage: ""
  emailSubject: ""
  smsSubject: ""
""")

EmailTemplates = yaml.safe_load("""
temp_password:
  subject: 'Temporary Password'
  message: 'Your username is {username} and your temporary password is {code}'
password_reset:
  subject: 'Password Reset'
  message: 'Your password reset code is {code}'
""")

class CustomMessageInlineCodeTest(unittest.TestCase):

    def setUp(self, email_templates = EmailTemplates):   
        self.env = {}
        self.env["EMAIL_TEMPLATES"] = json.dumps(email_templates)

    def test_admin_create_user(self,
                               event = AdminCreateUserEvent,
                               email_templates = EmailTemplates):
        with mock.patch.dict(os.environ, self.env):
            from pareto2.recipes.web_api.inline_code.custom_message import handler
            modevent = handler(event, context = None)
            response = modevent["response"]
            self.assertTrue("emailSubject" in response)
            self.assertEqual(response["emailSubject"],
                             email_templates["temp_password"]["subject"])
            self.assertTrue("emailMessage" in response)
            self.assertEqual(response["emailMessage"],
                             email_templates["temp_password"]["message"].replace("{code}", "{####}"))

    def test_forgot_password(self,
                             event = ForgotPasswordEvent,
                             email_templates = EmailTemplates):
        with mock.patch.dict(os.environ, self.env):
            from pareto2.recipes.web_api.inline_code.custom_message import handler
            modevent = handler(event, context = None)
            response = modevent["response"]
            self.assertTrue("emailSubject" in response)
            self.assertEqual(response["emailSubject"],
                             email_templates["password_reset"]["subject"])
            self.assertTrue("emailMessage" in response)
            self.assertEqual(response["emailMessage"],
                             email_templates["password_reset"]["message"].replace("{code}", "{####}"))

    def tearDown(self):
        pass
            
if __name__ == "__main__":
    unittest.main()
