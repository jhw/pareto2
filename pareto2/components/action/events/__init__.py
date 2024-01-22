from pareto2.components import hungarorise as H
from pareto2.components import resource

import importlib

"""
- no need for a module cache here as Python/importlib will check sys.modules
"""

def import_event_module(event,
                        paths=["pareto2.components.action.events.%s",
                               "ext.%s"]):
    for path in paths:
        try:
            return importlib.import_module(path % event["source"]["type"])
        except ModuleNotFoundError:
            pass
    raise RuntimeError("couldn't import event module for component %s" % event["source"]["type"])

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
        mod=import_event_module(event)
        return mod.init_event_rule(action, event)
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
