from cdk.components.actions import update_template as init_actions
from cdk.components.api import update_template as init_api
from cdk.components.bucket import update_template as init_bucket
from cdk.components.dashboards import update_template as init_dashboard
from cdk.components.errors import update_template as init_errors
from cdk.components.events import update_template as init_events
from cdk.components.layers import update_template as init_layers
from cdk.components.queues import update_template as init_queues
from cdk.components.routing import update_template as init_routing
from cdk.components.secrets import update_template as init_secrets
from cdk.components.table import update_template as init_table
from cdk.components.timers import update_template as init_timers
from cdk.components.users import update_template as init_users

from cdk.template import Template

from datetime import datetime

import os, yaml

StackNames=yaml.safe_load("""
- actions
- api
- bucket
- dashboard
- errors
- events
- layers
- queues
- routing
- secrets
- table
- timers
- users
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
        from cdk.metadata import Metadata
        md=Metadata.initialise(stagename)
        md.validate()
        template=init_template(md)
        template.dump_yaml(template.filename_yaml)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
