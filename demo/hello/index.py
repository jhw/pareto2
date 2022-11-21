"""
infra:
  events: []
  endpoint: {}
"""

import os

def handler(event, context,
            tablename=os.environ["DEMO_TABLE"],
            bucketname=os.environ["DEMO_BUCKET"]):
    print (event)
