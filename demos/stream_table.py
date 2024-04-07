from pareto2.recipes.stream_table import StreamTable
from pareto2.recipes.event_worker import EventWorker

import unittest, yaml

Worker = yaml.safe_load("""
alarm:
  period: 60
  threshold: 10
event:
  pattern:
    detail:
      eventName:
      - INSERT
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

class StreamTableTest(unittest.TestCase):

    def test_template(self):
        recipe = StreamTable(namespace = "app")
        worker = Worker
        worker["code"] = CodeBody
        recipe += EventWorker(namespace = "demo",
                              worker = worker)
        template = recipe.render()
        template.populate_parameters()
        template.dump_file(filename = "tmp/stream-table.json")
        parameters = list(template["Parameters"].keys())
        self.assertTrue(len(parameters) == 1)
        self.assertTrue("SlackWebhookUrl" in parameters)

if __name__ == "__main__":
    unittest.main()
