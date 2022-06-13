from cdk.components.actions import init_function, init_function_role

from cdk.components.queues import init_queue_binding

from cdk.components import hungarorise as H

from cdk.components import resource

"""
- defined as init_error_queue to distinguish from plain init_queue in queues.py
- latter is bound to error queue via redrive policy; former, being error queue itself, is not
"""

@resource
def init_error_queue(action):
    resourcename=H("%s-queue" % action["name"])
    return (resourcename, "AWS::SQS::Queue")

def init_component(action):
    resources=[]
    fns=[init_function,
         init_function_role,
         init_error_queue,
         init_queue_binding]
    for fn in fns:
        resource=fn(action)
        resources.append(resource)
    return resources

def init_resources(md):
    resources=[]
    action=md.errors
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
        from cdk.template import Template
        template=Template("errors")
        from cdk.metadata import Metadata
        md=Metadata.initialise(stagename)
        md.validate().expand()
        update_template(template, md)
        template.dump_yaml(template.filename_yaml)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
