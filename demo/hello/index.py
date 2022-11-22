"""
infra:
  events: 
  - name: whatevs
    pattern:
      hello: world
    source:
      name: demo
      type: bucket
  endpoint: 
    name: hello
    api: public
    path: hello-world
    method: GET
    parameters:
    - whatevs
  permissions:
  - foo:bar
  layers:
  - pyyaml
  size: medium
  timeout: medium
"""

import os

def handler(event, context,
            topicname=os.environ["DEMO_TOPIC"],
            tablename=os.environ["DEMO_TABLE"],
            bucketname=os.environ["DEMO_BUCKET"]):
    print (event)
