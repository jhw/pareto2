from pareto2.services import hungarorise as H
from pareto2.services import Resource

class Table(Resource):

    def __init__(self,
                 namespace,
                 attributes,
                 schema,
                 indexes = [],
                 billing_mode = "PAY_PER_REQUEST",
                 stream_type = None):
        super().__init__(namespace)
        self.attributes = attributes
        self.schema = schema
        self.indexes = indexes
        self.billing_mode = billing_mode
        self.stream_type = stream_type
        
    @property    
    def aws_properties(self):
        attributes = [{"AttributeName": attr["name"],
                       "AttributeType": attr["type"]}
                      for attr in self.attributes + self.indexes]
        schema = [{"AttributeName": attr["name"],
                   "KeyType": attr["type"]}
                  for attr in self.schema]
        props = {
            "AttributeDefinitions": attributes,
            "KeySchema": schema,
            "BillingMode": self.billing_mode
        }
        if self.indexes != []:
            gsi = [{"IndexName": index["name"],
                    "Projection": {"ProjectionType": "ALL"},
                    "KeySchema": [{"AttributeName": index["name"],
                                   "KeyType": "HASH"}]}
                   for index in self.indexes]
            props["GlobalSecondaryIndexes"] = gsi
        if self.stream_type:
            props["StreamSpecification"] = {"StreamViewType": self.stream_type}
        return props

    @property
    def visible(self):
        return True

class StreamingTable(Table):
    
    def __init__(self, namespace):
        super().__init__(namespace = namespace,
                         attributes = [{"name": "pk",
                                        "type": "S"},
                                       {"name": "sk",
                                        "type": "S"}],
                         schema =  [{"name": "pk",
                                     "type": "HASH"},
                                    {"name": "sk",
                                     "type": "RANGE"}],
                         stream_type = "NEW_AND_OLD_IMAGES")

