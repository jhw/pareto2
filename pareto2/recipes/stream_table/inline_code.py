import boto3, json, os

class Key:

    def __init__(self, pk, sk, event_name, diff_keys):
        self.pk = pk
        self.sk = sk
        self.event_name = event_name
        self.diff_keys = diff_keys

    def __str__(self):
        return "%s/%s/%s/%s" % (self.pk,
                                self.sk,
                                self.event_name,
                                "|".join(self.diff_keys))
    
"""
- EventBridge required fields are Source, DetailType, Detail
- record["eventName"] is used as DetailType
- eventName could be INSERT, MODIFY, DELETE
"""
    
class Entry:

    def __init__(self, key, records, source):
        self.key = key
        self.records = records
        self.source = source

    @property
    def entry(self):        
        detail = {"pk": self.key.pk,
                  "sk": self.key.sk,
                  "eventName": self.key.event_name,
                  "diffKeys": self.key.diff_keys,
                  "records": self.records}
        detail_type = self.key.event_name
        return {"Source": self.source,
                "DetailType": detail_type,
                "Detail": json.dumps(detail)}

"""
- keys are diff'ed because it's useful to be able to match on changed attributes if a record is being updated one attr at a time, and change on one attr triggers change in another
"""
    
def diff_keys(record):
    if not ("NewImage" in record["dynamodb"] and
            "OldImage" in record["dynamodb"]):
        return []        
    new_image={k: list(v.values())[0]
              for k, v in record["dynamodb"]["NewImage"].items()}
    old_image={k: list(v.values())[0]
              for k, v in record["dynamodb"]["OldImage"].items()}
    diff_keys=[]
    for k in new_image:
        if (k not in old_image or
            new_image[k] != old_image[k]):
            diff_keys.append(k)
    return sorted(diff_keys) # NB sort
    
def batch_records(records):
    keys, groups  =  {}, {}
    for record in records:
        pk = record["dynamodb"]["Keys"]["pk"]["S"]
        sk = record["dynamodb"]["Keys"]["sk"]["S"].split("#")[0]
        event_name = record["eventName"]
        diffed_keys = diff_keys(record)
        key = Key(pk = pk,
                  sk = sk,
                  event_name = event_name,
                  diff_keys = diffed_keys)
        strkey = str(key)
        if strkey not in keys:
            keys[strkey] = key
        groups.setdefault(strkey, [])
        groups[strkey].append(record)
    return [(key, groups[strkey])
            for strkey, key in keys.items()]

def handler(event, context,
            max_entries_per_batch = 10,
            max_payload_size = 256 * 1024):  # 256 KB
    source = os.environ["APP_TABLE"]
    groups = batch_records(event["Records"])    
    entries = [Entry(k, v, source).entry
               for k, v in groups]    
    events = boto3.client("events")
    batch, batch_size_bytes = [], 0
    for entry in entries:
        entry_size = len(json.dumps(entry))
        if entry_size > max_payload_size:
            raise RuntimeError(f"single entry size exceeds 256 KB: {entry}")
        if ((batch_size_bytes + entry_size) > max_payload_size or
            len(batch) >= max_entries_per_batch):
            if batch != []:
                events.put_events(Entries = batch)
            batch = [entry]
            batch_size_bytes = entry_size
        else:
            batch.append(entry)
            batch_size_bytes += entry_size        
    if batch != []:
        events.put_events(Entries=batch)


