from pareto2.cdk.components import hungarorise as H
from pareto2.cdk.components import resource

import json

@resource
def init_rule(action):
    def init_target(action):
        id={"Fn::Sub": "%s-rule-${AWS::StackName}" % action["name"]}
        input=json.dumps(action["timer"]["body"])
        arn={"Fn::GetAtt": [H("%s-function" % action["name"]), "Arn"]}
        return {"Id": id,
                "Input": input,
                "Arn": arn}        
    resourcename=H("%s-rule" % action["name"])
    target=init_target(action)
    scheduleexpr="rate(%s)" % action["timer"]["rate"]
    props={"Targets": [target],
           "ScheduleExpression": scheduleexpr}
    return (resourcename,
            "AWS::Events::Rule",
            props)

@resource
def init_permission(action):
    resourcename=H("%s-permission" % action["name"])
    sourcearn={"Fn::GetAtt": [H("%s-rule" % action["name"]), "Arn"]}
    funcname={"Ref": H("%s-function" % action["name"])}
    props={"Action": "lambda:InvokeFunction",
           "Principal": "events.amazonaws.com",
           "FunctionName": funcname,
           "SourceArn": sourcearn}
    return (resourcename,
            "AWS::Lambda::Permission",
            props)

def init_component(action):
    resources=[]
    for fn in [init_rule,
               init_permission]:
        resource=fn(action)
        resources.append(resource)
    return resources

def init_resources(md):
    resources=[]
    for action in md.actions:
        if "timer" in action:
            component=init_component(action)
            resources+=component
    return dict(resources)

def update_template(template, md):
    template["Resources"].update(init_resources(md))

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stagename")
        stagename=sys.argv[1]
        from pareto2.cdk.template import Template
        template=Template("timers")
        from pareto2.cdk.metadata import Metadata
        md=Metadata.initialise(stagename)
        md.validate().expand()
        update_template(template, md)
        template.dump_yaml(template.filename_yaml)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
