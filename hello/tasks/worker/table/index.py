"""
infra:
  type: worker
  event:
    type: table
    pattern:
      detail:
        pk:
        - hello
        sk:
        - world
        records:
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
    tablename = os.environ["APP_TABLE"]
