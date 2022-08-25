import boto3, json, math, os

### START TEMP CODE
os.environ.update({"ROUTER_EVENT_BUS": "my-router",
                   "BATCH_SIZE": "10",
                   "DEBUG": "true"})
### END TEMP CODE

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

    def __init__(self, key, records, context,
                 eventbusname=os.environ["ROUTER_EVENT_BUS"]):
        self.key=key
        self.records=records
        self.context=context
        self.eventbusname=eventbusname

    @property
    def entry(self):        
        detail={"ddb": {"pk": self.key.pk,
                        "sk": self.key.sk,
                        "eventName": self.key.eventname,
                        "diffKeys": self.key.diffkeys,
                        "records": self.records}}
        source=self.context.function_name
        detailtype=self.key.eventname
        return {"Source": source,
                "DetailType": detailtype,
                "Detail": json.dumps(detail),
                "EventBusName": self.eventbusname}

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
            # START TEMP CODE
            for item in batch:
                detail=json.loads(item["Detail"])
                print ("%s/%s/%s/%s [%i]" % (detail["ddb"]["pk"],
                                             detail["ddb"]["sk"],
                                             detail["ddb"]["eventName"],
                                             "|".join(detail["ddb"]["diffKeys"]),
                                             len(detail["ddb"]["records"])))
            # END TEMP CODE
            # START TEMP CODE
            # events.put_events(Entries=batch)
            # END TEMP CODE

if __name__=="__main__":
    event=json.loads(open("dev/ddb-event.json").read())
    from pareto2.test import Context
    context=Context("my-function")
    handler(event, context)
