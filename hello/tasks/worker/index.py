"""
infra:
  type: worker
  event:
    type: table
    pattern:
      detail:
        hello:
        - world
  alarm:
    period: 60
    threshold: 10
  permissions: []
  layers: []
  size: 0
  timeout: 30
"""

def handler(event, context = None):
    pass
