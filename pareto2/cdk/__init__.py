from pareto2.cdk.components.actions import update_template as init_actions
from pareto2.cdk.components.apis import update_template as init_apis
from pareto2.cdk.components.buckets import update_template as init_buckets
from pareto2.cdk.components.dashboards import update_template as init_dashboards
from pareto2.cdk.components.errors import update_template as init_errors
from pareto2.cdk.components.events import update_template as init_events
from pareto2.cdk.components.layers import update_template as init_layers
from pareto2.cdk.components.queues import update_template as init_queues
from pareto2.cdk.components.routers import update_template as init_routers
from pareto2.cdk.components.secrets import update_template as init_secrets
from pareto2.cdk.components.tables import update_template as init_tables
from pareto2.cdk.components.timers import update_template as init_timers
from pareto2.cdk.components.userpools import update_template as init_userpools

from pareto2.cdk.template import Template

from datetime import datetime

import os, yaml

StackNames=yaml.safe_load("""
- actions
- apis
- buckets
- dashboards
- errors
- events
- layers
- queues
- routers
- secrets
- tables
- timers
- userpools
""")

class Defaults(dict):

    @classmethod
    def initialise(self, stagename):
        filename="config/%s/defaults.yaml" % stagename
        if not os.path.exists(filename):
            raise RuntimeError("%s defaults does not exist" % stagename)
        return Defaults(yaml.safe_load(open(filename).read()))

    def __init__(self, items={}):
        dict.__init__(self, items)

def init_template(md,
                  name="main",
                  timestamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S"),
                  stacknames=StackNames):
    template=Template(name=name,
                      timestamp=timestamp)
    for stackname in stacknames:
        fn=eval("init_%s" % stackname)        
        fn(template=template,
           md=md)
    defaults=Defaults.initialise(md.stagename)
    template.autofill_parameters(defaults)
    return template

if __name__=="__main__":
    try:
        import sys
        if len(sys.argv) < 2:
            raise RuntimeError("please enter stagename")
        stagename=sys.argv[1]
        from pareto2.cdk.metadata import Metadata
        md=Metadata.initialise(stagename)
        md.validate()
        template=init_template(md)
        template.dump_yaml(template.filename_yaml)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
