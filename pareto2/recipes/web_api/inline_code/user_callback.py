import boto3, json

"""
This code is based on recipes/task_queue/inline_code.py
Send the full event and have clients match on the userpool as a source
Difference with SQS is that you don't need to iterate over records here, just send the whole event
Default assumption is that users are created one at a time and individual per- user events are generated
Don't bother checking for min size here there is no user component to the messages, ie can be resonably (??) sure they will fit inside the 256KB limit
"""

"""
All Cognito callbacks must return JSON else they will fail!
"""

def handler(event, context):
    entry = {"Detail": json.dumps(event),
             "DetailType": "event",
             "Source": event["userPoolId"]}
    events = boto3.client("events")
    batch = [entry]
    events.put_events(Entries=batch)
    return event # NB 
