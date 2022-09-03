from pareto2.core.components import hungarorise as H
from pareto2.core.components import resource

@resource
def init_topic(topic):
    resourcename=H("%s-topic" % topic["name"])
    endpoint={"Fn::GetAtt": [H("%s-function" % topic["action"]), "Arn"]}
    subscription={"Protocol": "lambda",
                  "Endpoint": endpoint}
    props={"Subscription": [subscription]}
    return (resourcename,
            "AWS::SNS::Topic",
            props)

@resource
def init_policy(topic):
    resourcename=H("%s-topic-policy" % topic["name"])
    statement={"Effect": "Allow",
               "Principal": {"Service": "sns.amazonaws.com"},
               "Action": ["sns:Publish"],
               "Resource": {"Ref": H("%s-topic" % topic["name"])}}
    policydoc={"Version": "2012-10-17",
               "Statement": [statement]}               
    props={"PolicyDocument": policydoc,
           "Topics": [{"Ref": H("%s-topic" % topic["name"])}]}
    return (resourcename,
            "AWS::SNS::TopicPolicy",
            props)

@resource
def init_permission(topic):
    resourcename=H("%s-topic-permission" % topic["name"])
    sourcearn={"Ref": H("%s-topic" % topic["name"])}
    funcname={"Ref": H("%s-function" % topic["action"])}
    props={"Action": "lambda:InvokeFunction",
           "Principal": "sns.amazonaws.com",
           "FunctionName": funcname,
           "SourceArn": sourcearn}
    return (resourcename,
            "AWS::Lambda::Permission",
            props)


def init_resources(components):
    resources=[]
    for topic in components["topics"]:
        for fn in [init_topic,
                   init_policy,
                   init_permission]:
            resources.append(fn(topic))
    return dict(resources)

def init_outputs(components):
    return {H("%s-topic" % topic["name"]): {"Value": {"Ref": H("%s-topic" % topic["name"])}}
            for topic in components["topics"]}

if __name__=="__main__":
    try:
        from pareto2.core.dsl import Config
        config=Config.initialise()
        from pareto2.core.template import Template
        template=Template("topics")
        template.resources.update(init_resources(config["components"]))
        template.outputs.update(init_outputs(config["components"]))
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
