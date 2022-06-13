from cdk.components import hungarorise as H
from cdk.components import resource
            
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
def init_queue(action, errors):
    resourcename=H("%s-queue" % action["name"])
    retries=action["retries"] if "retries" in action else 0
    dlqarn={"Fn::GetAtt": [H("%s-queue" % errors["name"]), "Arn"]}
    redrivepolicy={"deadLetterTargetArn": dlqarn,
                   "maxReceiveCount": 1+retries}
    props={"RedrivePolicy": redrivepolicy}
    return (resourcename,
            "AWS::SQS::Queue",
            props)

"""
- init_queue_binding needs **kwargs because queues.py wants to pass it errors arg but errors.py does not
"""

@resource
def init_queue_binding(action, **kwargs):
    resourcename=H("%s-queue-binding" % action["name"])
    funcname={"Ref": H("%s-function" % action["name"])}
    sourcearn={"Fn::GetAtt": [H("%s-queue" % action["name"]),
                              "Arn"]}
    props={"FunctionName": funcname,
           "EventSourceArn": sourcearn}
    return (resourcename,
            "AWS::Lambda::EventSourceMapping",
            props)

def init_component(action, errors):
    resources=[]
    for fn in [init_queue,
               init_queue_binding]:
        resource=fn(action, errors=errors)
        resources.append(resource)
    return resources

def init_resources(md):
    resources=[]
    errors=md.errors
    for action in md.actions:
        if ("queue" in action and
            action["queue"]):
            component=init_component(action, errors)
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
        from cdk.template import Template
        template=Template("queues")
        from cdk.metadata import Metadata
        md=Metadata.initialise(stagename)
        md.validate().expand()
        update_template(template, md)
        template.dump_yaml(template.filename_yaml)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
