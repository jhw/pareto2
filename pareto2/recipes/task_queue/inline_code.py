import boto3, json, math, os

"""
Need to expand body before sending to EventBridge so that different body fields can be pattern matched

Else there is no way for records sent to a single queue to be handled by different functions

EventBridge max batch size is 10
"""

def handler(event, context, batchsize = 10):
    source = os.environ["APP_QUEUE"]
    entries = [{"Detail": json.loads(record["body"]),
                "DetailType": "record-body",
                "Source": source}
               for record in event["Records"]]
    if entries != []:
        events = boto3.client("events")
        nbatches = math.ceil(len(entries)/batchsize)
        for i in range(nbatches):
            batch = entries[i*batchsize: (i+1)*batchsize]
            events.put_events(Entries = batch)

