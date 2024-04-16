"""
infra:
  type: worker
  event:
    type: unbound
    pattern:
      detail-type: 
      - whatevs
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
