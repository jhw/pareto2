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
"""

def handler(event, context = None):
    bucketname = os.environ["APP_BUCKET"]
