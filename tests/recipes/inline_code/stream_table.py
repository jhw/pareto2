from tests.recipes.inline_code import EventsTestMixin

from moto import mock_events, mock_sqs

import unittest.mock as mock

import json, os, unittest, yaml

SampleEvent = yaml.safe_load("""
Records:
  - eventID: "1"
    eventName: "INSERT"
    eventVersion: "1.0"
    eventSource: "aws:dynamodb"
    awsRegion: "us-east-1"
    dynamodb:
      ApproximateCreationDateTime: 1581045768
      Keys:
        pk:
          S: "LEAGUE#ENG1"
        sk:
          S: "TEAM#Liverpool"
      NewImage:
        pk:
          S: "LEAGUE#ENG1"
        sk:
          S: "TEAM#Liverpool"
        ground-name:
          S: "Anfield"
      StreamViewType: "NEW_AND_OLD_IMAGES"
      SequenceNumber: "123450000000000015824191036"
      SizeBytes: 112
    eventSourceARN: "arn:aws:dynamodb:us-east-1:123456789012:table/YourTableName/stream/2020-01-01T00:00:00.000"
""")

Rules = yaml.safe_load("""
- detail:
    pk:
    - prefix: LEAGUE
""")

@mock_events
@mock_sqs
class StreamTableInlineCodeTest(unittest.TestCase,
                                EventsTestMixin):

    def setUp(self, rules = Rules):        
        self.env = {}
        self.env["APP_TABLE"] = "app-table" # doesn't have to be mocked, is passed as source reference only
        self.setup_events(rules = rules)
    
    def test_code(self, event = SampleEvent):
        with mock.patch.dict(os.environ, self.env):
            from pareto2.recipes.stream_table.inline_code import handler
            handler(event, context = None)
            messages = self.drain_queue(queue = self.events_queue)
            self.assertTrue(len(messages) == 1)
            message = messages.pop()
            body = json.loads(message["Body"])
            self.assertTrue("detail" in body)
            detail = body["detail"]
            for k, v in [("eventName", "INSERT"),
                         ("pk", "LEAGUE#ENG1"),
                         ("sk", "TEAM")]:
                self.assertTrue(k in detail)
                self.assertEqual(detail[k], v)

    def tearDown(self):
        self.teardown_events()
            
if __name__ == "__main__":
    unittest.main()
