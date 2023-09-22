"""
infra:
  events: 
  - name: whatevs
    pattern:
      hello: world
    source:
      name: demo
      type: table
"""

import os

def handler(event, context,
            tablename=os.environ["DEMO_TABLE"]):
    print (event)
