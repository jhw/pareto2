class Table:
    
    def __init__(self, table, streamtype="NEW_AND_OLD_IMAGES", **kwargs):
        self.table = table
        self.streamtype = streamtype
        self.kwargs = kwargs

    @property
    def resource_name(self):
        return f"{self.table['name']}-table"

    @property
    def aws_resource_type(self):
        return "AWS::DynamoDB::Table"

    @property
    def aws_properties(self):
        attrs = [("pk", "S"), ("sk", "S")]
        if "indexes" in self.table:
            attrs += [(index["name"], index["type"]) for index in self.table["indexes"]]
        formatted_attrs = [{"AttributeName": name, "AttributeType": type_} for name, type_ in attrs]
        key_schema = [{"AttributeName": k, "KeyType": v} for k, v in [("pk", "HASH"), ("sk", "RANGE")]]
        props = {
            "AttributeDefinitions": formatted_attrs,
            "BillingMode": "PAY_PER_REQUEST",
            "KeySchema": key_schema
        }
        if "indexes" in self.table:
            gsi = [{"IndexName": f"{index['name']}-index",
                    "Projection": {"ProjectionType": "ALL"},
                    "KeySchema": [{"AttributeName": index["name"], "KeyType": "HASH"}]}
                   for index in self.table["indexes"]]
            props["GlobalSecondaryIndexes"] = gsi
        if "streaming" in self.table:
            props["StreamSpecification"] = {"StreamViewType": self.streamtype}
        return props

