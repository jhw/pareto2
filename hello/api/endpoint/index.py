"""
infra:
  type: endpoint
  method: GET
  path: public-get
  auth: public
  parameters:
  - message
  permissions:
  - s3:GetObject
  layers: []
  size: 0
  timeout: 30
"""

def handler(event, context = None):
    pass
