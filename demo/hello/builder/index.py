"""
infra:
  builder:
    bucket: demo
    notifications: whatevs
"""

import os

def handler(event, context):
    print (event)
