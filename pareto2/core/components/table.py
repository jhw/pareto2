from pareto2.core.components import hungarorise as H
from pareto2.core.components import uppercase as U
from pareto2.core.components import resource

FunctionCode="""import boto3, json, math, os

class Key:

    def __init__(self, pk, sk, eventname, diffkeys):
        self.pk=pk
        self.sk=sk
        self.eventname=eventname
        self.diffkeys=diffkeys

    def __str__(self):
        return "%s/%s/%s/%s" % (self.pk,
                                self.sk,
                                self.eventname,
                                "|".join(self.diffkeys))

class Entry:

    def __init__(self, key, records, context):
        self.key=key
        self.records=records
        self.context=context

    @property
    def entry(self):        
        detail={"pk": self.key.pk,
                "sk": self.key.sk,
                "eventName": self.key.eventname,
                "diffKeys": self.key.diffkeys,
                "records": self.records}
        source=self.context.function_name
        detailtype=self.key.eventname
        return {"Source": source,
                "DetailType": detailtype,
                "Detail": json.dumps(detail)}

def batch_records(records):
    def diff_keys(record):
        if not ("NewImage" in record["dynamodb"] and
                "OldImage" in record["dynamodb"]):
            return []        
        newimage={k: list(v.values())[0]
                  for k, v in record["dynamodb"]["NewImage"].items()}
        oldimage={k: list(v.values())[0]
                  for k, v in record["dynamodb"]["OldImage"].items()}
        diffkeys=[]
        for k in newimage:
            if (k not in oldimage or
                newimage[k]!=oldimage[k]):
                diffkeys.append(k)
        return sorted(diffkeys) # NB sort
    keys, groups = {}, {}
    for record in records:
        pk=record["dynamodb"]["Keys"]["pk"]["S"]
        sk=record["dynamodb"]["Keys"]["sk"]["S"].split("#")[0]
        eventname=record["eventName"]
        diffkeys=diff_keys(record)
        key=Key(pk=pk,
                sk=sk,
                eventname=eventname,
                diffkeys=diffkeys)
        strkey=str(key)
        if strkey not in keys:
            keys[strkey]=key
        groups.setdefault(strkey, [])
        groups[strkey].append(record)
    return [(key, groups[strkey])
            for strkey, key in keys.items()]

def handler(event, context,
            batchsize=os.environ["BATCH_SIZE"],
            debug=os.environ["DEBUG"]):
    batchsize=int(batchsize)
    debug=eval(debug.lower().capitalize())
    events=boto3.client("events")
    if debug:
        print ("--- records ---")
        print (json.dumps(event["Records"]))
    groups=batch_records(event["Records"])
    entries=[Entry(k, v, context).entry
             for k, v in groups]
    if debug:
        print ("--- entries ---")
        print (json.dumps(entries))
    if entries!=[]:
        nbatches=math.ceil(len(entries)/batchsize)
        for i in range(nbatches):
            batch=entries[i*batchsize:(i+1)*batchsize]
            events.put_events(Entries=batch)
"""

StreamType="NEW_AND_OLD_IMAGES"
StreamWindow=1
StreamRetries=3
StreamBatchSize=10

@resource
def init_table(table, streamtype=StreamType, **kwargs):
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
    props={"AttributeDefinitions": attrs,
           "BillingMode": "PAY_PER_REQUEST",
           "KeySchema": key,
           "GlobalSecondaryIndexes": gsi}
    if "streaming" in table:
        props["StreamSpecification"]={"StreamViewType": streamtype}
    return (resourcename,
            "AWS::DynamoDB::Table",
            props)

@resource
def init_streaming_binding(table,
                           streamwindow=StreamWindow,
                           streamretries=StreamRetries):
    resourcename=H("%s-table-mapping" % table["name"])
    funcname={"Ref": H("%s-table-streaming-function" % table["name"])}
    sourcearn={"Fn::GetAtt": [H("%s-table" % table["name"]),
                              "StreamArn"]}
    props={"FunctionName": funcname,
           "StartingPosition": "LATEST",
           "MaximumBatchingWindowInSeconds": streamwindow,
           "EventSourceArn": sourcearn,
           "MaximumRetryAttempts": streamretries}
    return (resourcename,
            "AWS::Lambda::EventSourceMapping",
            props)

@resource            
def init_streaming_function(table,
                            batchsize=StreamBatchSize,
                            code=FunctionCode):
    resourcename=H("%s-table-streaming-function" % table["name"])
    rolename=H("%s-table-streaming-function-role" % table["name"])
    code={"ZipFile": code}
    runtime={"Fn::Sub": "python${%s}" % H("runtime-version")}
    memorysize=H("memory-size-%s" % table["streaming"]["size"])
    timeout=H("timeout-%s" % table["streaming"]["timeout"])
    variables={}
    variables[U("batch-size")]=str(batchsize)
    variables[U("debug")]=str(table["streaming"]["debug"]) if "debug" in table["streaming"] else "false"
    props={"Role": {"Fn::GetAtt": [rolename, "Arn"]},
           "MemorySize": {"Ref": memorysize},
           "Timeout": {"Ref": timeout},
           "Code": code,
           "Handler": "index.handler",
           "Runtime": runtime,
           "Environment": {"Variables": variables}}
    return (resourcename, 
            "AWS::Lambda::Function",
            props)

@resource
def init_streaming_role(table,
                        permissions=["dynamodb:GetRecords",
                                     "dynamodb:GetShardIterator",
                                     "dynamodb:DescribeStream",
                                     "dynamodb:ListStreams",
                                     "events:PutEvents",
                                     "logs:CreateLogGroup",
                                     "logs:CreateLogStream",
                                     "logs:PutLogEvents"]):
    resourcename=H("%s-table-streaming-function-role" % table["name"])
    assumerolepolicydoc={"Version": "2012-10-17",
                         "Statement": [{"Action": "sts:AssumeRole",
                                        "Effect": "Allow",
                                        "Principal": {"Service": "lambda.amazonaws.com"}}]}
    policydoc={"Version": "2012-10-17",
               "Statement": [{"Action" : permission,
                              "Effect": "Allow",
                              "Resource": "*"}
                             for permission in sorted(permissions)]}
    policyname={"Fn::Sub": "%s-table-streaming-function-role-policy-${AWS::StackName}" % table["name"]}
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
    if "streaming" in table:
        for fn in [init_streaming_binding,
                   init_streaming_function,
                   init_streaming_role]:
            resource=fn(table)
            resources.append(resource)
    return resources

def init_resources(components):
    resources=[]
    for table in components["tables"]:
        component=init_component(table)
        resources+=component
    return dict(resources)

def init_outputs(components):
    return {H("%s-table" % table["name"]): {"Value": {"Ref": H("%s-table" % table["name"])}}
            for table in components["tables"]}
                               
if __name__=="__main__":
    try:
        from pareto2.core.dsl import Config
        config=Config.initialise()
        from pareto2.core.template import Template
        template=Template("tables")
        template.resources.update(init_resources(config["components"]))
        template.outputs.update(init_outputs(config["components"]))
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
