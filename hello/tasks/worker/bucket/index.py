"""
infra:
  type: worker
  event:
    type: bucket
    pattern:
      detail:
        bucket:
          name:
          - hello
        object:
          key:
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
    bucketname = os.environ["APP_BUCKET"]
