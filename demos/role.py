from pareto2.components import Template

from pareto2.aws.iam import Role

import json

if __name__=="__main__":
    template=Template()
    role=Role(namespace="my",
              permissions=["logs:*",
                           "s3:*"])
    template.add(role)
    print (json.dumps(template.render(),
                      indent=2))
    
