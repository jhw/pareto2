import boto3, yaml

TestTable=yaml.safe_load("""
indexes: []
name: test-table
stream:
  retries: 3
  batch:
    window: 1
  type: NEW_AND_OLD_IMAGES    
""")

class Pareto2DDBTestMixin:

    def setup_ddb(self,
                  tables=[TestTable]):
        def init_table(table):
            attrs=[{"AttributeName": name,
                    "AttributeType": type_}
                   for name, type_ in [("pk", "S"),
                                       ("sk", "S")]+[(index["name"], index["type"])
                                                     for index in table["indexes"]]]
            key=[{"AttributeName": k,
                  "KeyType": v}
                 for k, v in [("pk", "HASH"),
                              ("sk", "RANGE")]]
            props={"TableName": table["name"],
                   "BillingMode": "PAY_PER_REQUEST",
                   "AttributeDefinitions": attrs,
                   "KeySchema": key}
            if ("indexes" in table and
                table["indexes"]):
                gsi=[{"IndexName": "%s-index" % index["name"],
                      "Projection": {"ProjectionType": "ALL"},
                      "KeySchema": [{"AttributeName": index["name"],
                                     "KeyType": "HASH"}]}
                     for index in table["indexes"]]
                props["GlobalSecondaryIndexes"]=gsi
            return props
        def create_table(client, resource, table):            
            props=init_table(table)
            client.create_table(**props)
            return resource.Table(table["name"])
        client=boto3.client("dynamodb")
        resource=boto3.resource("dynamodb")
        self.tables=[create_table(client, resource, table)
                     for table in tables]
                
    def teardown_ddb(self):
        for table in self.tables:
            table.delete()

if __name__=="___main__":
    pass
