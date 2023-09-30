from pareto2.components import hungarorise as H
from pareto2.components import uppercase as U
from pareto2.components import resource

from pareto2.components.common.iam import policy_document, assume_role_policy_document

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
            events.put_events(Entries=batch)"""

StreamWindow=1
StreamRetries=3
StreamBatchSize=10

StreamingFunctionDefaults={"size": "default",
                           "timeout": "default",
                           "debug": "false"}

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

def streaming_defaults(fn):
    def wrapped(table, defaults=StreamingFunctionDefaults, **kwargs):
        if "streaming" in table:
            streaming=table["streaming"]
            for k, v in defaults.items():
                if k not in streaming:
                    streaming[k]=v
        return fn(table, **kwargs)
    return wrapped

@streaming_defaults
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
    policyname={"Fn::Sub": "%s-table-streaming-function-role-policy-${AWS::StackName}" % table["name"]}
    policydoc=policy_document(permissions)
    policies=[{"PolicyDocument": policydoc,
               "PolicyName": policyname}]
    props={"AssumeRolePolicyDocument": assume_role_policy_document(),
           "Policies": policies}
    return (resourcename,
            "AWS::IAM::Role",
            props)

if __name__=="__main__":
    pass
