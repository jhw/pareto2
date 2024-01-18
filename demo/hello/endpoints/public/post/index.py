"""
infra:
  endpoint: 
    api: public
    path: hello-world-public-post
    method: POST
    schema:
      properties:
        name:
          type: string
      required:
      - name
      type: object
"""

import os

def handler(event, context,
            tablename=os.environ["DEMO_TABLE"],
            bucketname=os.environ["DEMO_WEBSITE"]):
    print (event)
