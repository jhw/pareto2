from pareto2.components import Component

from pareto2.aws.iam import Role

import json

if __name__=="__main__":
    component=Component()
    role=Role(namespace="my",
              permissions=["logs:*",
                           "s3:*"])
    component.append(role)
    template=component.render()
    template.populate_parameters()
    print (json.dumps(template,
                      indent=2))
    
