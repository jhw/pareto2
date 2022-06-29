from pareto2.cdk.components.actions import init_function, init_role

from pareto2.cdk.components.queues import init_binding

from pareto2.cdk.components import hungarorise as H

from pareto2.cdk.components import resource

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
    """
    fns=[init_function,
         init_role,
         init_error_queue,
         init_binding]
    """
    fns=[init_function,
         init_role,
         init_error_queue]
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
        from pareto2.cdk.template import Template
        template=Template("errors")
        from pareto2.cdk.metadata import Metadata
        md=Metadata.initialise(stagename)
        md.validate().expand()
        update_template(template, md)
        template.dump_yaml(template.filename_yaml)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
