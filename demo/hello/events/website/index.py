"""
infra:
  events: 
  - name: whatevs
    pattern:
      hello: world
    source:
      name: demo
      type: website
"""

import os

def handler(event, context,
            websitename=os.environ["DEMO_WEBSITE"]):
    print (event)
