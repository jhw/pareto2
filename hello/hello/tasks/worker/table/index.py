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
"""

def handler(event, context = None):
    tablename = os.environ["APP_TABLE"]
