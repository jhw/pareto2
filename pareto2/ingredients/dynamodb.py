from pareto2.ingredients import hungarorise as H
from pareto2.ingredients import Resource

class Table(Resource):

    def __init__(self,
                 namespace,
                 attributes,
                 schema,                 
                 billing_mode = "PAY_PER_REQUEST",
                 stream_type = None):
        self.namespace = namespace
        self.attributes = attributes
        self.schema = schema
        self.billing_mode = billing_mode
        self.stream_type = stream_type
        
    @property    
    def aws_properties(self):
        attributes = [{"AttributeName": attr["name"],
                       "AttributeType": attr["type"]}
                      for attr in self.attributes]
        schema = [{"AttributeName": attr["name"],
                   "KeyType": attr["type"]}
                  for attr in self.schema]
        props = {
            "AttributeDefinitions": attributes,
            "KeySchema": schema,
            "BillingMode": self.billing_mode
        }
        if self.stream_type:
            props["StreamSpecification"] = {"StreamViewType": self.stream_type}
        return props

class SingleStreamingTable(Table):
    
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
