from pareto2.recipes.event_worker import EventWorker

import unittest, yaml

"""
Worker config doesn't have API in front of it hence doesn't benefit from API defaults
"""

Worker = yaml.safe_load("""
event:
  pattern:
    detail:
      hello:
       - world
layers:
  - foobar
""")

CodeBody="""
import logging

logger=logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context=None):
    logger.warning(str(event))
"""

class EventWorkerDemoTest(unittest.TestCase):
    
    def test_template(self):
        worker = Worker
        worker["code"] = CodeBody
        recipe = EventWorker(namespace = "my",
                             worker = worker)
        template = recipe.render()
        template.init_parameters()
        template.dump_file(filename = "tmp/event-worker.json")
        parameters = list(template["Parameters"].keys())
        self.assertTrue(len(parameters) == 2)
        for attr in ["SlackWebhookUrl",
                     "FoobarLayerArn"]:
            self.assertTrue(attr in parameters)

if __name__ == "__main__":
    unittest.main()
