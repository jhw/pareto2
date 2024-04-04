from pareto2.services import hungarorise as H
from pareto2.services import Resource

class Bucket(Resource):

    def __init__(self, namespace):
        super().__init__(namespace)

    @property
    def visible(self):
        return True

class StreamingBucket(Bucket):

    def __init__(self, namespace):
        super().__init__(namespace = namespace)
         
    @property
    def aws_properties(self):
        notconf = {"EventBridgeConfiguration": {"EventBridgeEnabled": True}}
        return {"NotificationConfiguration": notconf}

