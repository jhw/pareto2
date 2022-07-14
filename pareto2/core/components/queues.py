from pareto2.core.components import hungarorise as H
from pareto2.core.components import resource

"""
- queues are the only part of the messaging system which are tightly coupled to lambdas
- rest of the system is loosely coupled via eventbridge (*)
- (*) - except for table and bucket, which are singleton exceptions
- but you need queues because they are the only AWS primitive which offers delay functionality
- you don't want to overwhelm the target site :)
- given they are tightly coupled, makes more sense to have them located close to the functions themselves
- also worth noting that queue arns don't need to be exported anywhere; the only consumer is other functions which want to push messages onto those queues
"""

"""
- note that retries and dlq/destination are handled via Queue RedrivePolicy, and not Lambda EventSourceMappint
- EventSourceMapping supports neither DestinationConfig not MaximumRetryAttempts if source is sqs
"""

@resource
def init_queue(queue):
    resourcename=H("%s-queue" % queue["name"])
    props={}
    if "errors" in queue:
        dlqarn={"Fn::GetAtt": [H("%s-queue" % queue["errors"]), "Arn"]}
        retries=queue["retries"] if "retries" in queue else 0
        redrivepolicy={"deadLetterTargetArn": dlqarn,
                       "maxReceiveCount": 1+retries}
        props["RedrivePolicy"]=redrivepolicy
    return (resourcename,
            "AWS::SQS::Queue",
            props)

@resource
def init_binding(queue):
    resourcename=H("%s-queue-binding" % queue["name"])
    funcname={"Ref": H("%s-function" % queue["action"])}
    sourcearn={"Fn::GetAtt": [H("%s-queue" % queue["name"]),
                              "Arn"]}
    props={"FunctionName": funcname,
           "EventSourceArn": sourcearn}
    return (resourcename,
            "AWS::Lambda::EventSourceMapping",
            props)

def init_component(queue):
    resources=[]
    for fn in [init_queue,
               init_binding]:
        resource=fn(queue)
        resources.append(resource)
    return resources

def init_resources(md):
    resources=[]
    for queue in md.queues:
        component=init_component(queue)
        resources+=component
    return dict(resources)

def update_template(template, md):
    template.resources.update(init_resources(md))

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stagename")
        stagename=sys.argv[1]
        from pareto2.core.template import Template
        template=Template("queues")
        from pareto2.core.metadata import Metadata
        md=Metadata.initialise(stagename)
        md.validate().expand()
        update_template(template, md)
        template.dump_json(template.filename_json)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
