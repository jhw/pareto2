"""
infra:
  type: worker
  event:
    type: queue
    pattern:
      detail:
        hello:
        - world
  alarm:
    period: 60
    threshold: 10
  permissions: []
  layers: []
  size: 1024
  timeout: 30
"""

def handler(event, context = None):
    queuename = os.environ["APP_QUEUE"]

