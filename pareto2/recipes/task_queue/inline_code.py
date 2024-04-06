import boto3, json, math, os

"""
- EventBridge max batch size is 10
"""

def handler(event, context, batchsize = 10):
    source = os.environ["APP_QUEUE"]
    entries = [{"Detail": json.dumps(record),
                "DetailType": "record",
                "Source": source}
               for record in event["Records"]]
    if entries != []:
        events = boto3.client("events")
        nbatches = math.ceil(len(entries)/batchsize)
        for i in range(nbatches):
            batch = entries[i*batchsize: (i+1)*batchsize]
            events.put_events(Entries = batch)

