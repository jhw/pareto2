from pareto2.recipes.pip_builder import PipBuilder
from pareto2.recipes.event_worker import EventWorker

import unittest, yaml

Worker = yaml.safe_load("""
  event:
    pattern:
      source:
      - "aws.codebuild"
      detail-type:
      - "CodeBuild Build Phase Change"
      detail:
        project-name:
        - Ref: AppProject
        completed-phase:
        - SUBMITTED
        - PROVISIONING
        - DOWNLOAD_SOURCE
        - INSTALL
        - PRE_BUILD
        - BUILD
        - POST_BUILD
        - UPLOAD_ARTIFACTS
        - FINALIZING
        completed-phase-status:
        - TIMED_OUT
        - STOPPED
        - FAILED
        - SUCCEEDED
        - FAULT
        - CLIENT_ERROR
  permissions: []
""")

CodeBody="""
import logging

logger=logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context=None):
    logger.warning(str(event))
"""

class PipBuilderTest(unittest.TestCase):

    def test_template(self):
        recipe = PipBuilder(namespace = "app")
        worker = Worker
        worker["code"] = CodeBody
        recipe += EventWorker(namespace = "demo",
                              worker = worker)
        template = recipe.render()
        template.populate_parameters()
        template.dump_file(filename = "tmp/pip-builder.json")
        parameters = list(template["Parameters"].keys())
        self.assertTrue(len(parameters) == 1)
        self.assertTrue("SlackWebhookUrl" in parameters)

if __name__ == "__main__":
    unittest.main()
