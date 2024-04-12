from pareto2.recipes.task_queue import TaskQueue
from pareto2.recipes.event_worker import EventWorker

import unittest, yaml

Worker = yaml.safe_load("""
alarm:
  period: 60
  threshold: 10
event:
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

class TaskQueueTest(unittest.TestCase):

    def test_template(self):
        recipe = TaskQueue(namespace = "hello")
        worker = Worker
        worker["code"] = CodeBody
        recipe += EventWorker(namespace = "demo",
                              worker = worker)
        template = recipe.render()
        template.init_parameters()
        template.dump_file(filename = "tmp/task-queue.json")
        parameters = list(template["Parameters"].keys())                
        self.assertTrue(len(parameters) == 1)
        self.assertTrue("SlackWebhookUrl" in parameters)

if __name__ == "__main__":
    unittest.main()
