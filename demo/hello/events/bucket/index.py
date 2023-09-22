"""
infra:
  events: 
  - name: whatevs
    pattern:
      hello: world
    source:
      name: demo
      type: bucket
"""

import os

def handler(event, context,
            bucketname=os.environ["DEMO_BUCKET"]):
    print (event)
