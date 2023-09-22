"""
infra:
  events: 
  - name: whatevs
    pattern:
      hello: world
    source:
      name: demo
      type: builder
"""

import os

def handler(event, context,
            buildername=os.environ["DEMO_BUILDER"]):
    print (event)
