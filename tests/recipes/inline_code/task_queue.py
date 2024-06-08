from tests.recipes.inline_code import EventsTestMixin

from moto import mock_events, mock_sqs

import unittest.mock as mock

import json, os, unittest, yaml

SampleEvent = yaml.safe_load("""
Records:
  - messageId: "c80e8021-a70a-42c7-a470-796e1186f753"
    receiptHandle: "MbZj6wDWli+JvwwJaBV+3dcjk2HU4f1+7Zg="
    body: '{"hello": "world"}'
    attributes:
      ApproximateReceiveCount: "1"
      SentTimestamp: "1523232000000"
      SenderId: "123456789012"
      ApproximateFirstReceiveTimestamp: "1523232000001"
    messageAttributes:
      attribute1:
        stringValue: "attributeValue"
        binaryValue: "binaryValue"
        stringListValues:
          - "stringListValue1"
          - "stringListValue2"
        binaryListValues:
          - "binaryListValue1"
          - "binaryListValue2"
        dataType: "String"
    md5OfBody: "7b270e59b47ff90a553787216d55d91d"
    eventSource: "aws:sqs"
    eventSourceARN: "arn:aws:sqs:us-west-2:123456789012:MyQueue"
    awsRegion: "us-west-2"
""")

Rules = yaml.safe_load("""
- detail:
    hello:
    - world
""")

@mock_events
@mock_sqs
class TaskQueueInlineTest(unittest.TestCase,
                          EventsTestMixin):

    def setUp(self, rules = Rules):        
        self.env = {}
        self.env["APP_QUEUE"] = "app-queue" # doesn't have to be mocked, is passed as source reference only
        self.setup_events(rules = rules)
    
    def test_code(self, event = SampleEvent):
        with mock.patch.dict(os.environ, self.env):
            from pareto2.recipes.task_queue.inline_code import handler
            handler(event, context = None)
            messages = self.drain_queue(queue = self.events_queue)
            self.assertTrue(len(messages) == 1)
            message = messages.pop()
            body = json.loads(message["Body"])
            self.assertTrue("detail" in body)
            detail = body["detail"]
            self.assertTrue("hello" in detail)

    def tearDown(self):
        self.teardown_events()
            
if __name__ == "__main__":
    unittest.main()
