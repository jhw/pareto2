"""
infra:
  type: worker
  event:
    type: userpool
    pattern:
      detail:
        hello: world
"""

def handler(event, context = None):
    user_pool_id = os.environ["APP_USER_POOL"]
