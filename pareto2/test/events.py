import boto3, json

class Pareto2EventsTestMixin:

    def setup_events(self, rules):
        self.events, self.sqs = (boto3.client("events"),
                                 boto3.client("sqs"))
        self.events_queue=queue=self.sqs.create_queue(QueueName="events-queue")
        queueattrs=self.sqs.get_queue_attributes(QueueUrl=queue["QueueUrl"],
                                                 AttributeNames=["QueueArn"])["Attributes"]
        for i, rule in enumerate(rules):
            rulename, targetid = ("rule-%i" % i,
                                  "target-%i" % i)
            self.events.put_rule(Name=rulename,
                                 State="ENABLED",
                                 EventPattern=json.dumps(rule))
            self.events.put_targets(Rule=rulename,
                                    Targets=[{"Id": targetid,
                                              "Arn": queueattrs["QueueArn"]}])
            
    def drain_queue(self, queue):
        messages=[]
        while True:
            resp=self.sqs.receive_message(QueueUrl=queue["QueueUrl"])
            if ("Messages" in resp and
                resp["Messages"]!=[]):
                messages+=resp["Messages"]
            else:
                break
        return messages
            
    def teardown_events(self):
        for rule in self.events.list_rules(NamePrefix="rule")["Rules"]:
            for target in self.events.list_targets_by_rule(Rule=rule["Name"]):
                targetid="target-%i" % int(rule["Name"].split("-")[-1])
                self.events.remove_targets(Rule=rule["Name"],
                                           Ids=[targetid])
            self.events.delete_rule(Name=rule["Name"])
        self.sqs.delete_queue(QueueUrl=self.events_queue["QueueUrl"])
            
if __name__=="___main__":
    pass
