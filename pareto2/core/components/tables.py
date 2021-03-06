from pareto2.core.components import hungarorise as H
from pareto2.core.components import resource

"""
- Table is named, like Bucket, for consistency of treatment of storage sources
- unlike Bucket, no need to name table because of SourceArn considerations
- however if you want to specify resources in Function Roles, will need a defined name so that Arn can be constructed as a string
"""

@resource
def init_table(table, **kwargs):
    resourcename=H("%s-table" % table["name"])
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
    name={"Fn::Sub": "%s-table-${AWS::StackName}-${AWS::Region}" % table["name"]}
    props={"AttributeDefinitions": attrs,
           "BillingMode": "PAY_PER_REQUEST",
           "KeySchema": key,
           "GlobalSecondaryIndexes": gsi,
           "TableName": name}
    if "action" in table:
        stream={"StreamViewType": table["stream"]["type"]}
        props["StreamSpecification"]=stream
    return (resourcename,
            "AWS::DynamoDB::Table",
            props)

@resource
def init_binding(table):
    resourcename=H("%s-table-mapping" % table["name"])
    funcname={"Ref": H("%s-function" % table["action"])}
    sourcearn={"Fn::GetAtt": [H("%s-table" % table["name"]),
                              "StreamArn"]}
    window=table["stream"]["batch"]["window"]
    retries=table["stream"]["retries"]
    props={"FunctionName": funcname,
           "StartingPosition": "LATEST",
           "MaximumBatchingWindowInSeconds": window,
           "EventSourceArn": sourcearn,
           "MaximumRetryAttempts": retries}
    if "errors" in table:
        destarn={"Fn::GetAtt": [H("%s-queue" % table["errors"]), "Arn"]}
        destconfig={"OnFailure": {"Destination": destarn}}
        props["DestinationConfig"]=destconfig
    return (resourcename,
            "AWS::Lambda::EventSourceMapping",
            props)

def init_resources(md):
    resources=[]
    for table in md.tables:
        resources.append(init_table(table))
        if "action" in table:
            resources.append(init_binding(table))
    return dict(resources)

def init_outputs(md):
    return {H("%s-table" % table["name"]): {"Value": {"Ref": H("%s-table" % table["name"])}}
            for table in md.tables}
                               
def update_template(template, md):
    template.resources.update(init_resources(md))
    template.outputs.update(init_outputs(md))
    
if __name__=="__main__":
    try:
        from pareto2.core.template import Template
        template=Template("table")
        from pareto2.core.metadata import Metadata
        md=Metadata.initialise()        
        md.validate().expand()
        update_template(template, md)
        template.dump(template.filename)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
