import boto3, json, math, os

class Key:

    def __init__(self, pk, sk, eventname):
        self.pk = pk
        self.sk = sk
        self.eventname = eventname

    def __str__(self):
        return "%s/%s/%s" % (self.pk,
                             self.sk,
                             self.eventname)

"""
- NB record["eventName"] is used as DetailType
- NB context.function_name is used as Source
"""
    
class Entry:

    def __init__(self, key, records, context):
        self.key = key
        self.records = records
        self.context = context

    @property
    def entry(self):        
        detail = {"pk": self.key.pk,
                  "sk": self.key.sk,
                  "eventName": self.key.eventname,
                  "records": self.records}
        source = self.context.function_name
        detailtype = self.key.eventname
        return {"Source": source,
                "DetailType": detailtype,
                "Detail": json.dumps(detail)}

def batch_records(records):
    keys, groups  =  {}, {}
    for record in records:
        pk = record["dynamodb"]["Keys"]["pk"]["S"]
        sk = record["dynamodb"]["Keys"]["sk"]["S"].split("#")[0]
        eventname = record["eventName"]
        key = Key(pk = pk,
                  sk = sk,
                  eventname = eventname)
        strkey = str(key)
        if strkey not in keys:
            keys[strkey] = key
        groups.setdefault(strkey, [])
        groups[strkey].append(record)
    return [(key, groups[strkey])
            for strkey, key in keys.items()]

def handler(event, context, batchsize = 10):
    batchsize = int(batchsize)
    events = boto3.client("events")
    groups = batch_records(event["Records"])
    entries = [Entry(k, v, context).entry
               for k, v in groups]
    if entries! = []:
        nbatches = math.ceil(len(entries)/batchsize)
        for i in range(nbatches):
            batch = entries[i*batchsize: (i+1)*batchsize]
            events.put_events(Entries = batch)

