from botocore.exceptions import ClientError

from moto import mock_events, mock_sqs

import boto3, json, sys

def warn(*args, **kwargs):
    pass
import warnings
warnings.warn=warn

class Router:

    def __init__(self, name, patterns=[]):
        self.name=name
        self.patterns=patterns

    @property
    def event_bus_name(self):
        return "%s-event-bus" % self.name

    @property
    def target_queue_name(self):
        return "%s-target-queue" % self.name

    @property
    def rule_prefix(self):
        return "%s-rule-prefix" % self.name

@mock_events
@mock_sqs
def is_valid(pattern, event, routername="my-router"):
    def init_events(events, sqs, router):
        events.create_event_bus(Name=router.event_bus_name)
        statement=[{"Effect": "Allow",
                    "Principal": {"Service": "events.amazonaws.com"},
                    "Action": "sqs:SendMessage",
                    "Resource": "*"}]
        policy=json.dumps({"Version": "2012-10-17",
                           "Statement": [statement]})
        queue=sqs.create_queue(QueueName=router.target_queue_name,
                               Attributes={"Policy": policy})
        queueattrs=sqs.get_queue_attributes(QueueUrl=queue["QueueUrl"])
        queuearn=queueattrs["Attributes"]["QueueArn"]
        for i, pattern in enumerate(router.patterns):
            """
            - because accidental list pattern detail seems to match everything, regardless of list contents
            """
            if not isinstance(pattern["detail"], dict):
                raise RuntimeError("pattern detail must be a dict")
            rulename="%s-%i" % (router.rule_prefix, i+1)
            ruletargetid="%s-target-%i" % (router.rule_prefix, i+1)
            events.put_rule(EventBusName=router.event_bus_name,
                            Name=rulename,
                            State="ENABLED",
                            EventPattern=json.dumps(pattern))
            events.put_targets(EventBusName=router.event_bus_name,
                               Rule=rulename,
                               Targets=[{"Id": ruletargetid,
                                         "Arn": queuearn}])
    def fetch_queue(sqs, queueurl):
        queue=sqs.get_queue_attributes(QueueUrl=queueurl)["Attributes"]
        queue["QueueName"]=queue["QueueArn"].split(":")[-1]
        return queue                    
    def list_queues(sqs):
        return [fetch_queue(sqs, queueurl)
                for queueurl in sqs.list_queues()["QueueUrls"]]
    def drain_queue(sqs, queueurl, nmax=100):
        messages, count = [], 0
        while True:
            resp=sqs.receive_message(QueueUrl=queueurl)
            if ("Messages" not in resp or
                count > nmax):
                break
            messages+=resp["Messages"]
            count+=1
        return messages
    def test_pattern(events, sqs, router, event,
                     source="my-source",
                     detailtype="my-detail-type"):
        """
        - matching will always fail without Source and DetailType attrs
        """
        item={"Source": source,
              "DetailType": detailtype,
              "Detail": json.dumps(event),
              "EventBusName": router.event_bus_name}
        events.put_events(Entries=[item])
        messages=drain_queue(sqs, router.target_queue_name)
        return len(messages)==1
    def delete_events(events, router):
        for rule in events.list_rules(EventBusName=router.event_bus_name)["Rules"]:
            targets=events.list_targets_by_rule(Rule=rule["Name"])["Targets"]
            for target in targets:
                events.remove_targets(Rule=rule["Name"],
                                      Ids=[target["Id"]])
            events.delete_rule(Name=rule["Name"])
        events.delete_event_bus(Name=router.event_bus_name)
    def delete_queues(sqs):
        for queue in list_queues(sqs):
            sqs.delete_queue(QueueUrl=queue["QueueName"])
    events, sqs = (boto3.client("events"),
                   boto3.client("sqs"))
    router=Router(name=routername,
                  patterns=[{"detail": pattern}]) # NB detail
    init_events(events, sqs, router)
    resp=test_pattern(events, sqs, router, event)
    """
    - always clean stuff up just in case mock stuff is not properly enabled
    - this stuff should probably be in a finally block
    """
    delete_events(events, router)
    delete_queues(sqs)
    return resp
    
def parse_json(name, value):
    try:
        return json.loads(value)
    except:
        raise RuntimeError("error parsing %s" % name)
    
if __name__=="__main__":
    try:
        if len(sys.argv) < 3:
            raise RuntimeError("please enter pattern, event")
        pattern=parse_json("pattern", sys.argv[1])
        event=parse_json("event", sys.argv[2])
        print (is_valid(pattern, event))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
    except ClientError as error:
        print ("Error: %s" % str(error))
