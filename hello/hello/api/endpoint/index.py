"""
infra:
  type: endpoint
  method: GET
  path: hello-get
  auth: private
  parameters:
  - message
  permissions:
  - s3:GetObject
"""

def handler(event, context = None):
    pass
