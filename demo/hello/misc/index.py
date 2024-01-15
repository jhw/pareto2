"""
infra:
  indexes: 
  - name: hello-index
    type: S
    table: demo
  layers:
  - pyyaml
  permissions:
  - foo:bar
  size: medium
  timeout: medium
"""

import os

def handler(event, context,
            tablename=os.environ["DEMO_TABLE"],
            bucketname=os.environ["DEMO_BUCKET"]):
    print (event)
