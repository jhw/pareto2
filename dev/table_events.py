import boto3, json, math, os

### START TEMP CODE
os.environ.update({"ROUTER_EVENT_BUS": "my-router",
                   "BATCH_SIZE": "10"})
### END TEMP CODE

class Entry:

    def __init__(self, key, records, context,
                 eventbusname=os.environ["ROUTER_EVENT_BUS"]):
        self.pk, self.sk, self.eventname = key
        self.records=records
        self.context=context
        self.eventbusname=eventbusname

    @property
    def entry(self):
        detail={"ddb": {"pk": self.pk,
                        "sk": self.sk,
                        "records": self.records}}
        detailtype=self.eventname
        source=self.context.function_name
        return {"Source": source,
                "DetailType": detailtype,
                "Detail": json.dumps(detail),
                "EventBusName": self.eventbusname}

def batch_records(records):
    groups={}
    for record in records:
        if "NewImage" not in record["dynamodb"]:
            continue
        pk=record["dynamodb"]["Keys"]["pk"]["S"]
        sk=record["dynamodb"]["Keys"]["sk"]["S"].split("#")[0]
        key=(pk, sk, record["eventName"])
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
            # START TEMP CODE
            # events.put_events(Entries=batch)
            for item in batch:
                print (item)
            # END TEMP CODE

if __name__=="__main__":
    from pareto2.test import Context
    event=json.loads(open("dev/ddb-event.json").read())
    context=Context("my-function")
    handler(event, context)
