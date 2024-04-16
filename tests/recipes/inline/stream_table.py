from tests.recipes.inline import EventsTestMixin

from moto import mock_events, mock_sqs

import unittest.mock as mock

import os, unittest, yaml

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

@mock_events
@mock_sqs
class StreamTableInlineTest(unittest.TestCase,
                            EventsTestMixin):

    def setUp(self):        
        self.env = {}
        self.env["APP_TABLE"] = "app-table" # doesn't have to be mocked, is passed as source reference only
        self.setup_events(rules = [])
    
    def test_code(self, event = SampleEvent):
        with mock.patch.dict(os.environ, self.env):
            from pareto2.recipes.stream_table.inline_code import handler
            handler(event, context = None)

    def tearDown(self):
        self.teardown_events()
            
if __name__ == "__main__":
    unittest.main()
