from pareto2.recipes.web_api import WebApi

import unittest, yaml

def load_body(filename):
    absfilepath = "/".join(__file__.split("/")[:-1]+[filename])
    with open(absfilepath) as f:
        body = f.read()
    return body

EchoGetBody, EchoPostBody = (load_body("echo_get.py"),
                             load_body("echo_post.py"))

Endpoints = yaml.safe_load("""
- method: GET
  path: public-get
  auth: public
  parameters:
  - message
  permissions:
  - s3:GetObject
- method: POST
  path: public-post
  auth: public
  permissions:
  - s3:GetObject
  - s3:PutObject
- method: GET
  path: private-get
  auth: private
  parameters:
  - message
  permissions:
  - s3:GetObject
- method: POST
  path: private-post
  auth: private
  permissions:
  - s3:GetObject
  - s3:PutObject
""")

UserPool = yaml.safe_load("""
identity_providers:
  - google
attributes:
  - name: foo
    type: str
    value: bar
templates:
  temp_password:
    subject: "whatevs"
    message: "whatevs"
  password_reset:
    subject: "whatevs"
    message: "whatevs"
""")

class WebApiDemoTest(unittest.TestCase):

    def test_template(self):
        endpoints = {endpoint["path"]:endpoint
                     for endpoint in Endpoints}
        for path, endpoint in endpoints.items():
            if "get" in path:
                endpoint["code"] = EchoGetBody
            elif "post" in path:
                endpoint["code"] = EchoPostBody
            else:
                raise RuntimeError("couldn't embed code body for endpoint %s" % path)
        recipe = WebApi(namespace = "app",
                        endpoints = list(endpoints.values()),
                        userpool = UserPool)
        template = recipe.render()
        template.init_parameters()
        template.dump_file(filename = "tmp/web-api.json")
        parameters = list(template["Parameters"].keys())
        self.assertTrue(len(parameters) == 7)
        for attr in ["DomainName",
                     "RegionalCertificateArn",
                     "SlackWebhookUrl",
                     "GoogleClientId",
                     "GoogleClientSecret",
                     "ProdUiEndpoint",
                     "DevUiEndpoint"]:
            self.assertTrue(attr in parameters)

if __name__ == "__main__":
    unittest.main()
