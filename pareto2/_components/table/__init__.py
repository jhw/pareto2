from pareto2.components import hungarorise as H
from pareto2.components import resource

from pareto2.components.table.streaming import init_streaming_binding, init_streaming_function, init_streaming_role

StreamType="NEW_AND_OLD_IMAGES"

@resource
def init_table(table, streamtype=StreamType, **kwargs):
    resourcename=H("%s-table" % table["name"])
    attrs=[("pk", "S"),
           ("sk", "S")]
    if "indexes" in table:
        attrs+=[(index["name"], index["type"])
                for index in table["indexes"]]
    formattedattrs=[{"AttributeName": name,
                     "AttributeType": type_}
                    for name, type_ in attrs]
    keyschema=[{"AttributeName": k,
                "KeyType": v}
               for k, v in [("pk", "HASH"),
                            ("sk", "RANGE")]]
    props={"AttributeDefinitions": formattedattrs,
           "BillingMode": "PAY_PER_REQUEST",
           "KeySchema": keyschema}
    if "indexes" in table:
        gsi=[{"IndexName": "%s-index" % index["name"],
              "Projection": {"ProjectionType": "ALL"},
              "KeySchema": [{"AttributeName": index["name"],
                             "KeyType": "HASH"}]}
             for index in table["indexes"]]
        props["GlobalSecondaryIndexes"]=gsi
    if "streaming" in table:
        props["StreamSpecification"]={"StreamViewType": streamtype}
    return (resourcename,
            "AWS::DynamoDB::Table",
            props)

def render_resources(table):
    resources=[]
    for fn in [init_table]:
        resource=fn(table)
        resources.append(resource)
    if "streaming" in table:
        for fn in [init_streaming_binding,
                   init_streaming_function,
                   init_streaming_role]:
            resource=fn(table)
            resources.append(resource)
    return dict(resources)

def render_outputs(table):
    return {H("%s-table" % table["name"]): {"Value": {"Ref": H("%s-table" % table["name"])}}}
                               
if __name__=="__main__":
    pass
