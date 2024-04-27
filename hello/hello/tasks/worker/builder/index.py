"""
infra:
  type: worker
  event:
    type: builder
    pattern:
      detail:
        project-name:
        - hello
        completed-phase:
        - SUBMITTED
        completed-phase-status:
        - TIMED_OUT
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
