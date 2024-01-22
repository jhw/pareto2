from pareto2.components import hungarorise as H

def init_event_rule(action, event):
    pattern={}
    if "topic" in event:
        pattern["detail-type"]=[event["topic"]] # NB temp as topic is currently defined as a string
    if "pattern" in event:
        pattern["detail"]=event["pattern"]
    if "source" in event:
        pattern["source"]=[{"Ref": H("%s-table-streaming-function" % event["source"]["name"])}]
    return pattern
