from pareto2.cdk.components import hungarorise as H
from pareto2.cdk.components import resource

"""
- Table is named, like Bucket, for consistency of treatment of storage sources
- unlike Bucket, no need to name table because of SourceArn considerations
- however if you want to specify resources in Function Roles, will need a defined name so that Arn can be constructed as a string
"""

@resource
def init_table(table, **kwargs):
    resourcename=H(table["name"])
    attrs=[{"AttributeName": name,
            "AttributeType": type_}
           for name, type_ in [("pk", "S"),
                               ("sk", "S")]+[(index["name"], index["type"])
                                             for index in table["indexes"]]]
    key=[{"AttributeName": k,
          "KeyType": v}
         for k, v in [("pk", "HASH"),
                      ("sk", "RANGE")]]
    gsi=[{"IndexName": "%s-index" % index["name"],
          "Projection": {"ProjectionType": "ALL"},
          "KeySchema": [{"AttributeName": index["name"],
                         "KeyType": "HASH"}]}
         for index in table["indexes"]]
    stream={"StreamViewType": table["stream"]["type"]}
    name={"Fn::Sub": "%s-${AWS::StackName}-${AWS::Region}" % table["name"]}
    props={"AttributeDefinitions": attrs,
           "BillingMode": "PAY_PER_REQUEST",
           "KeySchema": key,
           "GlobalSecondaryIndexes": gsi,
           "StreamSpecification": stream,
           "TableName": name}
    return (resourcename,
            "AWS::DynamoDB::Table",
            props)

@resource
def init_table_mapping(table, errors):
    resourcename=H("%s-mapping" % table["name"])
    funcname={"Ref": H("%s-function" % table["name"])}
    sourcearn={"Fn::GetAtt": [H(table["name"]),
                              "StreamArn"]}
    destarn={"Fn::GetAtt": [H("%s-queue" % errors["name"]), "Arn"]}
    destconfig={"OnFailure": {"Destination": destarn}}
    window=table["stream"]["batch"]["window"]
    retries=table["stream"]["retries"]
    props={"FunctionName": funcname,
           "StartingPosition": "LATEST",
           "MaximumBatchingWindowInSeconds": window,
           "EventSourceArn": sourcearn,
           "DestinationConfig": destconfig,
           "MaximumRetryAttempts": retries}
    return (resourcename,
            "AWS::Lambda::EventSourceMapping",
            props)

def init_resources(md):
    return dict([fn(md.table,
                    errors=md.errors)
                 for fn in [init_table,
                            init_table_mapping]])

def init_outputs(md):
    table=md.table
    return {H(table["name"]): {"Value": {"Ref": H(table["name"])}}}
                               
def update_template(template, md):
    template["Resources"].update(init_resources(md))
    template["Outputs"].update(init_outputs(md))
    
if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stagename")
        stagename=sys.argv[1]
        from pareto2.cdk.template import Template
        template=Template("table")
        from pareto2.cdk.metadata import Metadata
        md=Metadata.initialise(stagename)        
        md.validate().expand()
        update_template(template, md)
        template.dump_yaml(template.filename_yaml)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
