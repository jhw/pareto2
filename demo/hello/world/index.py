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
  queue: {}
  permissions:
  - foo:bar
  secrets:
  - name: whatevs
    value: stuff
  topic: {}
  timer: 
    rate: "1 minute"
    body:
      hello: world   
  size: medium
  timeout: medium
"""

import os

def handler(event, context,
            tablename=os.environ["DEMO_TABLE"],
            bucketname=os.environ["DEMO_BUCKET"]):
    print (event)
