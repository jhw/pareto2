from pareto2.services import hungarorise as H
from pareto2.services import Resource

class Bucket(Resource):

    @property
    def visible(self):
        return True

class StreamBucket(Bucket):

    @property
    def aws_properties(self):
        notconf = {"EventBridgeConfiguration": {"EventBridgeEnabled": True}}
        return {"NotificationConfiguration": notconf}

