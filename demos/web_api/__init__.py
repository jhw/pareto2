from pareto2.recipes.web_api import WebApi

import json, os, yaml

EchoGetBody, EchoPostBody = (open("demos/web_api/echo_get.py").read(),
                             open("demos/web_api/echo_post.py").read())

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

if __name__ == "__main__":
    try:
        endpoints = {endpoint["path"]:endpoint
                     for endpoint in Endpoints}
        for path, endpoint in endpoints.items():
            if "get" in path:
                endpoint["code"] = EchoGetBody
            elif "post" in path:
                endpoint["code"] = EchoPostBody
            else:
                raise RuntimeError("couldn't embed code body for endpoint %s" % path)
        if not os.path.exists("tmp"):
            os.mkdir("tmp")
        template = WebApi(namespace = "app",
                          endpoints = list(endpoints.values())).render()
        template.populate_parameters()
        with open(f"tmp/web-api.json", 'w') as f:
            f.write(json.dumps(template,
                               sort_keys = True,
                               indent = 2))
        print (", ".join(list(template["Parameters"].keys())))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
