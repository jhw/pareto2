import boto3, yaml

TestTopic=yaml.safe_load("""
name: test-topic
""")

class Pareto2SNSTestMixin:

    def setup_sns(self, topics=[TestTopic]):
        self.sns=boto3.client("sns")
        self.topics=[self.sns.create_topic(Name=topic["name"])
                     for topic in topics]

    def teardown_sns(self):
        for topic in self.topics:
            self.sns.delete_topic(TopicArn=topic["TopicArn"])
        
if __name__=="___main__":
    pass
