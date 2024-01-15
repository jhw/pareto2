from pareto2.components import hungarorise as H
from pareto2.components import resource

def init_bucket_event_rule(action, event):
    pattern={}
    if "topic" in event:
        pattern["detail-type"]=[event["topic"]] # NB temp as topic is currently defined as a string
    if "pattern" in event:
        pattern["detail"]=event["pattern"]
    if "source" in event:
        pattern.setdefault("detail", {})
        pattern["detail"].setdefault("bucket", {})
        pattern["detail"]["bucket"]["name"]=[{"Ref": H("%s-bucket" % event["source"]["name"])}]
        pattern["source"]=["aws.s3"]
    return pattern

def init_table_event_rule(action, event):
    pattern={}
    if "topic" in event:
        pattern["detail-type"]=[event["topic"]] # NB temp as topic is currently defined as a string
    if "pattern" in event:
        pattern["detail"]=event["pattern"]
    if "source" in event:
        pattern["source"]=[{"Ref": H("%s-table-streaming-function" % event["source"]["name"])}]
    return pattern

def init_website_event_rule(action, event):
    pattern={}
    if "topic" in event:
        pattern["detail-type"]=[event["topic"]] # NB temp as topic is currently defined as a string
    if "pattern" in event:
        pattern["detail"]=event["pattern"]
    if "source" in event:
        pattern.setdefault("detail", {})
        pattern["detail"].setdefault("bucket", {})
        pattern["detail"]["bucket"]["name"]=[{"Ref": H("%s-website" % event["source"]["name"])}]
        pattern["source"]=["aws.s3"]
    return pattern

def init_unbound_event_rule(action, event):
    pattern={}
    if "topic" in event:
        pattern["detail-type"]=[event["topic"]] # NB temp as topic is currently defined as a string
    if "pattern" in event:
        pattern["detail"]=event["pattern"]
    return pattern

def render_event_rule(fn):
    def init_target(action, event, nmax=64):
        id=("%s-%s-target" % (action["name"],
                              event["name"]))[:nmax] # NB
        arn={"Fn::GetAtt": [H("%s-function" % action["name"]), "Arn"]}
        return {"Id": id,
                "Arn": arn}
    def wrapped(action, event):
        resourcename=H("%s-%s-event-rule" % (action["name"],
                                             event["name"]))
        target=init_target(action, event)
        pattern=fn(action, event)
        if pattern=={}:
            raise RuntimeError("%s/%s event config is blank" % (action["name"],
                                                                event["name"]))
        props={"EventPattern": pattern,
               "Targets": [target],
               "State": "ENABLED"}
        return (resourcename,
                "AWS::Events::Rule",
                props)
    return wrapped

@resource
@render_event_rule
def init_event_rule(action, event):
    if "source" in event:
        if event["source"]["type"]=="bucket":
            return init_bucket_event_rule(action, event)
        elif event["source"]["type"]=="table":
            return init_table_event_rule(action, event)
        elif event["source"]["type"]=="website":
            return init_website_event_rule(action, event)        
        else:
            raise RuntimeError("no event rule handler for type %s" % event["type"])
    else:
        return init_unbound_event_rule(action, event)
    
@resource
def init_event_rule_permission(action, event):
    resourcename=H("%s-%s-event-rule-permission" % (action["name"],
                                                    event["name"]))
    sourcearn={"Fn::GetAtt": [H("%s-%s-event-rule" % (action["name"],
                                                      event["name"])), "Arn"]}
    funcname={"Ref": H("%s-function" % action["name"])}
    props={"Action": "lambda:InvokeFunction",
           "Principal": "events.amazonaws.com",
           "FunctionName": funcname,
           "SourceArn": sourcearn}
    return (resourcename,
            "AWS::Lambda::Permission",
            props)

if __name__=="__main__":
    pass
