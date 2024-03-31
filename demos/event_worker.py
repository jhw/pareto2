from pareto2.recipes.event_worker import EventWorker

import yaml

Worker = yaml.safe_load("""
  events:
  - name: whatevs
    pattern:
      detail:
        hello:
         - world
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
    template.dump_file(filename = "tmp/event-worker.json")
    print (", ".join(list(template["Parameters"].keys())))

