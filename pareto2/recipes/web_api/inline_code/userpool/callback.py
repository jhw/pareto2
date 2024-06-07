import boto3, json, os

"""
This code is based on recipes/task_queue/inline_code.py
Send the full event and have clients match on the userpool as a source
Difference with SQS is that you don't need to iterate over records here, just send the whole event
Default assumption is that users are created one at a time and individual per- user events are generated
"""

def handler(event, context,
            max_payload_size = 256 * 1024):  # 256 KB
    source = os.environ["APP_USERPOOL"]
    entry = {"Detail": event,
             "DetailType": "event",
             "Source": source}
    entry_size = len(json.dumps(entry))
    if entry_size > max_payload_size:
        raise RuntimeError(f"entry size exceeds 256 KB: {entry}")
    events = boto3.client("events")
    batch = [entry]
    events.put_events(Entries=batch)
                
