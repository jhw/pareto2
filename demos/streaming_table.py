from pareto2.recipes.streaming_table import StreamingTable
from pareto2.recipes.event_worker import EventWorker

import json, os, yaml

"""
NB source value is expected to be inserted into pattern at expanded/CI level and not provided by app definition
"""

Worker = yaml.safe_load("""
  events:
  - name: foobar
    pattern:
      detail:
        pk: 
        - prefix: LEAGUE
      source:
      - Ref: AppTable
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
    worker = Worker
    worker["code"] = CodeBody
    recipe += EventWorker(namespace = "demo",
                          worker = worker)
    template = recipe.render()
    template.populate_parameters()
    if not os.path.exists("tmp"):
        os.mkdir("tmp")
    with open("tmp/streaming-table.json", 'w') as f:
        f.write(json.dumps(template,
                           sort_keys = True,
                           indent = 2))

