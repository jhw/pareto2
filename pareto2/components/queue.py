from pareto2.components import hungarorise as H
from pareto2.components import resource

@resource
def init_queue(queue):
    resourcename=H("%s-queue" % queue["name"])
    props={}
    return (resourcename,
            "AWS::SQS::Queue",
            props)

@resource
def init_binding(queue):
    resourcename=H("%s-queue-binding" % queue["name"])
    funcname={"Ref": H("%s-function" % queue["action"])}
    sourcearn={"Fn::GetAtt": [H("%s-queue" % queue["name"]), "Arn"]}
    batchsize = 1 if "batch" not in queue else queue["batch"]    
    props={"FunctionName": funcname,
           "EventSourceArn": sourcearn,
           "BatchSize": batchsize}
    return (resourcename,
            "AWS::Lambda::EventSourceMapping",
            props)

def render_resources(queue):
    resources=[]
    for fn in [init_queue,
               init_binding]:
        resource=fn(queue)
        resources.append(resource)
    return dict(resources)

def render_outputs(queue):
    return {H("%s-queue" % queue["name"]): {"Value": {"Ref": H("%s-queue" % queue["name"])}}}

if __name__=="__main__":
    pass
