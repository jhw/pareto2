"""
infra:
  type: worker
  # event: {} # event is missing for a topic worker
  alarm:
    period: 60
    threshold: 10
  permissions: []
  layers: []
  size: 1024
  timeout: 30
"""

def handler(event, context = None):
    pass
