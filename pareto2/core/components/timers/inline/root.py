import boto3, json, os

def handler(event, context,
            interval=os.environ["INTERVAL"],
            queueurl=os.environ["QUEUE_URL"]):
    sqs=boto3.client("sqs")
    items=json.loads(event["body"]) # not sure if this is correct
    for i, item in enumerate(items):
        delay=i*int(interval)
        sqs.send_message(QueueUrl=queueurl,
                         DelaySeconds=delay,
                         MessageBody=json.dumps(item))
