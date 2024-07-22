"""
infra:
  type: worker
  event:
    type: userpool
    pattern:
      detail:
        hello: world
  alarm:
    period: 60
    threshold: 10
  permissions: []
  layers: []
  size: 1024
  timeout: 30
"""

def handler(event, context = None):
    user_pool_id = os.environ["APP_USER_POOL"]
