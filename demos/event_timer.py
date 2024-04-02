from pareto2.recipes.event_timer import EventTimer

import unittest, yaml

Timer = yaml.safe_load("""
  event:
    schedule: "rate(1 minute)"
""")

CodeBody="""
import logging

logger=logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context=None):
    logger.warning(str(event))
"""

class EventTimerTest(unittest.TestCase):
    
    def test_template(self):
        timer = Timer
        timer["code"] = CodeBody
        recipe = EventTimer(namespace = "my",
                            timer = timer)
        template = recipe.render()
        template.populate_parameters()
        template.dump_file(filename = "tmp/event-timer.json")
        parameters = list(template["Parameters"].keys())
        self.assertTrue(len(parameters) == 1)
        self.assertTrue("SlackWebhookUrl" in parameters)

if __name__ == "__main__":
    unittest.main()
