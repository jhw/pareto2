from pareto2.recipes.streaming_table import StreamingTable
from pareto2.recipes.event_worker import EventWorker

import unittest, yaml

Worker = yaml.safe_load("""
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

class StreamingTableTest(unittest.TestCase):

    def test_template(self):
        recipe = StreamingTable(namespace = "app")
        worker = Worker
        worker["code"] = CodeBody
        recipe += EventWorker(namespace = "demo",
                              worker = worker)
        template = recipe.render()
        template.populate_parameters()
        template.dump_file(filename = "tmp/streaming-table.json")
        parameters = list(template["Parameters"].keys())
        self.assertTrue(len(parameters) == 1)
        self.assertTrue("SlackWebhookUrl" in parameters)

if __name__ == "__main__":
    unittest.main()
