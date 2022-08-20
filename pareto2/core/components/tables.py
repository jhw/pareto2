from pareto2.core.components import hungarorise as H
from pareto2.core.components import resource

FunctionCode="""import boto3, json, math, os

class Entry:

    def __init__(self, key, records, context,
                 eventbusname=os.environ["ROUTER_EVENT_BUS"]):
        self.pk, self.sk = key
        self.records=records
        self.context=context
        self.eventbusname=eventbusname

    @property
    def entry(self):
        detail={"ddb": {"pk": self.pk,
                        "sk": self.sk,
                        "records": self.records}}
        detailtype=self.records[0]["eventName"]
        source=self.context.function_name
        return {"Source": source,
                "DetailType": detailtype,
                "Detail": json.dumps(detail),
                "EventBusName": self.eventbusname}

def batch_records(records):
    groups={}
    for record in records:
        pk=record["dynamodb"]["Keys"]["pk"]["S"]
        sk=record["dynamodb"]["Keys"]["sk"]["S"].split("#")[0]
        key=(pk, sk)
        groups.setdefault(key, [])
        groups[key].append(record)
    return groups

def handler(event, context,
            batchsize=os.environ["BATCH_SIZE"]):
    batchsize=int(batchsize)
    events=boto3.client("events")
    groups=batch_records(event["Records"])
    entries=[Entry(k, v, context).entry
             for k, v in groups.items()]
    if entries!=[]:
        nbatches=math.ceil(len(entries)/batchsize)
        for i in range(nbatches):
            batch=entries[i*batchsize:(i+1)*batchsize]
            events.put_events(Entries=batch)
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

@resource            
def init_function(table,
                  batchsize=StreamingBatchSize,
                  code=FunctionCode):
    resourcename=H("%s-table-function" % table["name"])
    rolename=H("%s-table-function-role" % table["name"])
    code={"ZipFile": code}
    runtime={"Fn::Sub": "python${%s}" % H("runtime-version")}
    variables={}
    variables[U("router-event-bus")]={"Ref": H("%s-router-event-bus" % table["router"])}
    variables[U("batch-size")]=str(batchsize)
    props={"Role": {"Fn::GetAtt": [rolename, "Arn"]},
           "Code": code,
           "Handler": "index.handler",
           "Runtime": runtime,
           "Environment": {"Variables": variables}}
    return (resourcename, 
            "AWS::Lambda::Function",
            props)

@resource
def init_role(table,
              permissions=["dynamodb", "events", "logs"]):
    resourcename=H("%s-table-function-role" % table["name"])
    assumerolepolicydoc={"Version": "2012-10-17",
                         "Statement": [{"Action": "sts:AssumeRole",
                                        "Effect": "Allow",
                                        "Principal": {"Service": "lambda.amazonaws.com"}}]}
    policydoc={"Version": "2012-10-17",
               "Statement": [{"Action" : "%s:*" % permission,
                              "Effect": "Allow",
                              "Resource": "*"}
                             for permission in sorted(permissions)]}
    policyname={"Fn::Sub": "%s-table-function-role-policy-${AWS::StackName}" % table["name"]}
    policies=[{"PolicyDocument": policydoc,
               "PolicyName": policyname}]
    props={"AssumeRolePolicyDocument": assumerolepolicydoc,
           "Policies": policies}
    return (resourcename,
            "AWS::IAM::Role",
            props)

def init_component(table):
    resources=[]
    for fn in [init_table]:
        resource=fn(table)
        resources.append(resource)
    if "stream" in table:
        for fn in [init_binding,
                   init_function,
                   init_role]:
            resource=fn(table)
            resources.append(resource)
    return resources

def init_resources(md):
    resources=[]
    for table in md.tables:
        component=init_component(table)
        resources+=component
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
        template=Template("tables")
        from pareto2.core.metadata import Metadata
        md=Metadata.initialise()        
        md.validate().expand()
        update_template(template, md)
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
