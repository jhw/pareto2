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
  layers: []
  size: 1024
  timeout: 30
"""

def handler(event, context = None):
    pass
