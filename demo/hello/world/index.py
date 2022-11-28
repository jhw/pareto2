"""
infra:
  callbacks:
  - type: oncreate
    body:
      hello: world
  events: 
  - name: whatevs
    pattern:
      hello: world
    source:
      name: demo
      type: bucket
  endpoint: 
    api: public
    path: hello-world
    method: GET
    parameters:
    - whatevs
  indexes: 
  - name: hello-index
    type: S
    table: demo
  layers:
  - pyyaml
  permissions:
  - foo:bar
  secrets:
  - name: whatevs
    value: stuff
  size: medium
  timeout: medium
"""

import os

def handler(event, context,
            topicname=os.environ["DEMO_TOPIC"],
            tablename=os.environ["DEMO_TABLE"],
            bucketname=os.environ["DEMO_BUCKET"]):
    print (event)
