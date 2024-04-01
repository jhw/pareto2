from pareto2.recipes.event_worker import EventWorker

import unittest, yaml

Worker = yaml.safe_load("""
  event:
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

class EventWorkerTest(unittest.TestCase):
    
    def test_template(self):
        worker = Worker
        worker["code"] = CodeBody
        template = EventWorker(namespace = "my",
                               worker = worker).render()
        template.populate_parameters()
        template.dump_file(filename = "tmp/event-worker.json")
        parameters = list(template["Parameters"].keys())
        self.assertTrue(len(parameters) == 1)
        self.assertTrue("SlackWebhookUrl" in parameters)

if __name__ == "__main__":
    unittest.main()
