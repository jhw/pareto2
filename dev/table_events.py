import boto3, json, math, os

### START TEMP CODE
os.environ.update({"ROUTER_EVENT_BUS": "my-router",
                   "BATCH_SIZE": "10"})
### END TEMP CODE

class Key:

    def __init__(self, pk, sk, eventname):
        self.pk=pk
        self.sk=sk
        self.eventname=eventname

    def __str__(self):
        return "%s/%s/%s" % (self.pk,
                             self.sk,
                             self.eventname)

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
                        "records": self.records}}
        source=self.context.function_name
        detailtype=self.key.eventname
        return {"Source": source,
                "DetailType": detailtype,
                "Detail": json.dumps(detail),
                "EventBusName": self.eventbusname}

def batch_records(records):
    keys, groups = {}, {}
    for record in records:
        if "NewImage" not in record["dynamodb"]:
            continue
        pk=record["dynamodb"]["Keys"]["pk"]["S"]
        sk=record["dynamodb"]["Keys"]["sk"]["S"].split("#")[0]
        eventname=record["eventName"]
        key=Key(pk=pk,
                sk=sk,
                eventname=eventname)
        strkey=str(key)
        if strkey not in keys:
            keys[strkey]=key
        groups.setdefault(strkey, [])
        groups[strkey].append(record)
    return [(key, groups[strkey])
            for strkey, key in keys.items()]

def handler(event, context,
            batchsize=os.environ["BATCH_SIZE"]):
    batchsize=int(batchsize)
    events=boto3.client("events")
    groups=batch_records(event["Records"])
    entries=[Entry(k, v, context).entry
             for k, v in groups]
    if entries!=[]:
        nbatches=math.ceil(len(entries)/batchsize)
        for i in range(nbatches):
            batch=entries[i*batchsize:(i+1)*batchsize]
            # START TEMP CODE
            # events.put_events(Entries=batch)
            # END TEMP CODE
            # START TEMP CODE
            for item in batch:
                detail=json.loads(item["Detail"])
                print ("%s records" % len(detail["ddb"]["records"]))
            # END TEMP CODE

if __name__=="__main__":
    from pareto2.test import Context
    event=json.loads(open("dev/ddb-event.json").read())
    context=Context("my-function")
    handler(event, context)
