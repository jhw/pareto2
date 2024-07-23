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
"""

def handler(event, context = None):
    bucketname = os.environ["APP_BUCKET"]
