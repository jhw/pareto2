from pareto2.recipes.streaming_table import StreamingTable
from pareto2.recipes.event_worker import EventWorker

import json, os, yaml

Worker = yaml.safe_load("""
  events:
  - name: foobar
    pattern:
      detail:
        hello: 
        - world
  permissions:
  - s3:GetObject
""")

CodeBody="""
import logging

logger=logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context=None):
    logger.warning(str(event))
"""

if __name__ == "__main__":
    recipe = StreamingTable(namespace = "app")
    _worker = Worker
    _worker["code"] = CodeBody
    recipe += EventWorker(namespace = "demo",
                          worker = _worker)
    template = recipe.render()
    template.populate_parameters()
    if not os.path.exists("tmp"):
        os.mkdir("tmp")
    with open("tmp/streaming-table.json", 'w') as f:
        f.write(json.dumps(template,
                           sort_keys = True,
                           indent = 2))

