from pareto2.recipes.task_queue import TaskQueue
from pareto2.recipes.event_worker import EventWorker

import json, os, yaml

"""
NB source value is expected to be inserted into pattern at expanded/CI level and not provided by app definition
"""

Worker = yaml.safe_load("""
  events:
  - name: whatevs
    pattern:
      source:
      - Ref: HelloQueue
""")

CodeBody="""
import logging

logger=logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context=None):
    logger.warning(str(event))
"""

if __name__ == "__main__":
    recipe = TaskQueue(namespace = "hello")
    worker = Worker
    worker["code"] = CodeBody
    recipe += EventWorker(namespace = "demo",
                          worker = worker)
    template = recipe.render()
    template.populate_parameters()
    if not os.path.exists("tmp"):
        os.mkdir("tmp")
    with open("tmp/task-queue.json", 'w') as f:
        f.write(json.dumps(template,
                           sort_keys = True,
                           indent = 2))
    print (", ".join(list(template["Parameters"].keys())))
