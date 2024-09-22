import boto3
import json
import os

"""
SQS passes body as a string; this is simply forwarded to EventBridge as the Detail (string) value

In this manner, body attributes can be pattern matched and picked up by different Lambdas, event though they have originated from the same single queue
"""

def handler(event, context,
            max_entries_per_batch = 10,
            max_payload_size = 256 * 1024):  # 256 KB
    source = os.environ["APP_QUEUE"]
    entries = [{"Detail": record["body"],
                "DetailType": "record-body",
                "Source": source}
               for record in event["Records"]]
    events = boto3.client("events")
    batch, batch_size_bytes = [], 0
    for entry in entries:
        entry_size = len(json.dumps(entry))
        if entry_size > max_payload_size:
            raise RuntimeError(f"single entry size exceeds 256 KB: {entry}")
        if ((batch_size_bytes + entry_size) > max_payload_size or
            len(batch) >= max_entries_per_batch):
            if batch != []:
                events.put_events(Entries = batch)
            batch = [entry]
            batch_size_bytes = entry_size
        else:
            batch.append(entry)
            batch_size_bytes += entry_size        
    if batch != []:
        events.put_events(Entries=batch)
                
