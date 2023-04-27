import boto3, yaml

TestTopic=yaml.safe_load("""
name: test-topic
""")

class Pareto2SNSTestMixin:

    def setup_sns(self, topics=[TestTopic]):
        self.sns, self.sqs = (boto3.client("sns"),
                              boto3.client("sqs"))
        self.topics, self.topicqueues = [], []
        for _topic in topics:
            queue=self.sqs.create_queue(QueueName="%s-queue" % _topic["name"])
            queueattrs=self.sqs.get_queue_attributes(QueueUrl=queue["QueueUrl"],
                                                     AttributeNames=["QueueArn"])["Attributes"]
            self.topicqueues.append(queue)
            topic=self.sns.create_topic(Name=_topic["name"])
            self.topics.append(topic)
            self.sns.subscribe(TopicArn=topic["TopicArn"],
                               Protocol="sqs",
                               Endpoint=queueattrs["QueueArn"])

    def drain_queue(self, queueurl):
        messages=[]
        while True:
            resp=self.sqs.receive_message(QueueUrl=queueurl)
            if ("Messages" in resp and
                resp["Messages"]!=[]):
                messages+=resp["Messages"]
            else:
                break
        return messages
            
    def teardown_sns(self):
        for topic in self.topics:
            self.sns.delete_topic(TopicArn=topic["TopicArn"])
        for queue in self.topicqueues:
            self.sqs.delete_queue(QueueUrl=queue["QueueUrl"])
            
if __name__=="___main__":
    pass

