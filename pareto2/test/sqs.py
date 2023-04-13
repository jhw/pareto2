import boto3, yaml

TestQueue=yaml.safe_load("""
name: test-queue
""")

class Pareto2SQSTestMixin:

    def setup_sqs(self, queues=[TestQueue]):
        self.sqs=boto3.client("sqs")
        self.queues=[self.sqs.create_queue(QueueName=queue["name"])
                     for queue in queues]

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
        
    def teardown_sqs(self):        
        for queue in self.queues:
            self.sqs.delete_queue(QueueUrl=queue["QueueUrl"])
        
if __name__=="___main__":
    pass
