from pareto2.recipes.event_worker import EventWorker

import json, os, yaml

Worker = yaml.safe_load("""
  events:
  - name: whatevs
    pattern:
      detail:
        eventName:
         - INSERT
        pk:
         prefix:
         - LEAGUE
""")

CodeBody="""
import logging

logger=logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context=None):
    logger.warning(str(event))
"""

if __name__ == "__main__":
    worker = Worker
    worker["code"] = CodeBody
    template = EventWorker(namespace = "my",
                           worker = worker).render()
    template.populate_parameters()
    if not os.path.exists("tmp"):
        os.mkdir("tmp")
    with open("tmp/event-worker.json", 'w') as f:
        f.write(json.dumps(template,
                           sort_keys = True,
                           indent = 2))
    print (", ".join(list(template["Parameters"].keys())))

