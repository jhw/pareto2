"""
infra:
  type: timer
  event:
    schedule: "rate(1 minute)"
  permissions: []
  layers: []
  size: -1
  timeout: 30
"""

def handler(event, context = None):
    pass
