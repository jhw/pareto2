from pareto2.recipes.task_queue import TaskQueue
from pareto2.recipes.event_worker import EventWorker

import yaml

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
    template.dump_file(filename = "tmp/task-queue.json")
    print (", ".join(list(template["Parameters"].keys())))
