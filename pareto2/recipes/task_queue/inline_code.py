import boto3, math, os

"""
SQS passes body as a string; this is simply forwarded to EventBridge as the Detail (string) value

In this manner, body attributes can be pattern matched and picked up by different Lambdas, event though they have originated from the same single queue

EventBridge max batch size is 10
"""

def handler(event, context, batchsize = 10):
    source = os.environ["APP_QUEUE"]
    entries = [{"Detail": record["body"],
                "DetailType": "record-body",
                "Source": source}
               for record in event["Records"]]
    if entries != []:
        events = boto3.client("events")
        nbatches = math.ceil(len(entries)/batchsize)
        for i in range(nbatches):
            batch = entries[i*batchsize: (i+1)*batchsize]
            events.put_events(Entries = batch)

