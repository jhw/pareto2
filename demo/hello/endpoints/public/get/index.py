"""
infra:
  endpoint: 
    api: public
    path: hello-world-public-get
    method: GET
    parameters:
    - whatevs
"""

import os

def handler(event, context,
            tablename=os.environ["DEMO_TABLE"],
            bucketname=os.environ["DEMO_BUCKET"]):
    print (event)
