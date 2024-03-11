from pareto2.aws import hungarorise as H
from pareto2.aws import Resource

class Bucket(Resource):

    def __init__(self, namespace):
        self.namespace = namespace

class StreamingBucket(Bucket):

    def __init__(self, namespace):
        super().__init__(namespace)
         
    @property
    def aws_properties(self):
        notconf = {"EventBridgeConfiguration": {"EventBridgeEnabled": True}}
        return {"NotificationConfiguration": notconf}
