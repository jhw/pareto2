from pareto2.aws import hungarorise as H
from pareto2.aws import Resource

class Bucket(Resource):

    def __init__(self, component_name):
        self.component_name = component_name

    @property
    def aws_properties(self):
        notconf = {"EventBridgeConfiguration": {"EventBridgeEnabled": True}}
        return {"NotificationConfiguration": notconf}
