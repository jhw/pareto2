"""
infra:
  type: worker
  event:
    type: queue
    pattern:
      detail:
        hello: world
"""

def handler(event, context = None):
    queuename = os.environ["APP_QUEUE"]

