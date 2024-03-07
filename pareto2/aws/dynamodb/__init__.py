from pareto2.aws import hungarorise as H
from pareto2.aws import Resource

class Table(Resource):
    
    def __init__(self, component_name, indexes, streamtype="NEW_AND_OLD_IMAGES"):
        self.component_name = component_name
        self.indexes = indexes
        self.streamtype = streamtype

    @property
    def aws_properties(self):
        attrs = [("pk", "S"), ("sk", "S")]
        if "indexes" in self.table:
            attrs += [(index["name"], index["type"]) for index in self.indexes]
        formatted_attrs = [{"AttributeName": name, "AttributeType": type_} for name, type_ in attrs]
        key_schema = [{"AttributeName": k, "KeyType": v} for k, v in [("pk", "HASH"), ("sk", "RANGE")]]
        props = {
            "AttributeDefinitions": formatted_attrs,
            "BillingMode": "PAY_PER_REQUEST",
            "KeySchema": key_schema
        }
        if "indexes" in self.table:
            gsi = [{"IndexName": H(f"{index['name']}-index"),
                    "Projection": {"ProjectionType": "ALL"},
                    "KeySchema": [{"AttributeName": index["name"], "KeyType": "HASH"}]}
                   for index in self.indexes]
            props["GlobalSecondaryIndexes"] = gsi
        if "streaming" in self.table:
            props["StreamSpecification"] = {"StreamViewType": self.streamtype}
        return props

