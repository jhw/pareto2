from pareto2.services import hungarorise as H

from pareto2.services.iam import *

import importlib

L = importlib.import_module("pareto2.services.lambda")

import re

"""
- LogNamespace is a singleton namespace 
"""

LogNamespace, LogLevels = "logs", ["warning", "error"]

class Template(dict):

    def __init__(self, resources):
        dict.__init__(self, {"Parameters": {},
                             "Resources": dict([resource.render()
                                                for resource in resources]),
                             "Outputs": {H(resource.resource_name): {"Value": {"Ref": H(resource.resource_name)}}
                                         for resource in resources
                                         if resource.visible}})

    def populate_parameters(self):
        ids = list(self["Resources"].keys())
        refs = self.refs
        self["Parameters"].update({ref: {"Type": "String"}
                                   for ref in refs
                                   if ref not in ids})
        
    @property
    def node_refs(self):
        def is_ref(key, element):
            return (key == "Ref" and
                    type(element) == str and
                    "::" not in str(element))
        def is_getatt(key, element):
            return (key == "Fn::GetAtt" and
                    type(element) == list and
                    len(element) == 2 and
                    type(element[0]) == str and
                    type(element[1]) == str)
        def is_depends(key, element):
            return (key == "DependsOn" and
                    type(element) == list)
        def filter_refs(element, refs):
            if isinstance(element, list):
                for subelement in element:
                    filter_refs(subelement, refs)
            elif isinstance(element, dict):
                for key, subelement in element.items():
                    if is_ref(key, subelement):
                        # print (key, subelement)
                        refs.add(subelement)
                    elif is_getatt(key, subelement):
                        # print (key, subelement[0])
                        refs.add(subelement[0])
                    elif is_depends(key, subelement):
                        # print (key, set(subelement))
                        refs.update(subelement)
                    else:
                        filter_refs(subelement, refs)
        refs = set()
        filter_refs(self["Resources"], refs)
        return refs

    @property
    def inline_refs(self):
        def filter_expressions(text):
            return [tok[2:-1]
                    for tok in re.findall("\\$\\{\\w+\\}", text)
                    if tok != tok.lower()]
        def filter_refs(element, refs):
            if isinstance(element, list):
                for subelement in element:
                    if isinstance(subelement, str):
                        refs.update(set(filter_expressions(subelement)))
                    else:
                        filter_refs(subelement, refs)
            elif isinstance(element, dict):
                for key, subelement in element.items():
                    if isinstance(subelement, str):
                        refs.update(set(filter_expressions(subelement)))
                    else:
                        filter_refs(subelement, refs)
        refs = set()
        filter_refs(self, refs)
        return refs

    @property
    def refs(self):
        refs = set()
        refs.update(self.node_refs)
        refs.update(self.inline_refs)
        return refs    
    
"""
- a recipe is just a very thin wrapper around list of resources
- it does not contain its own namespace in state because it may need to operate across a number of namespaces, particularly parent/child (eg api/endpoint)
"""

class Recipe(list):

    def __init__(self):
        list.__init__(self)

    def render(self):
        return Template(self)

    def function_kwargs(self, endpoint):
        kwargs = {}
        for attr in ["code",
                     "handler",
                     "memory",
                     "timeout",
                     "runtime",
                     "layers"]:
            if attr in endpoint:
                kwargs[attr] = endpoint[attr]
        return kwargs
    
    def wildcard_override(fn):
        def wrapped(self, *args, **kwargs):
            permissions=fn(self, *args, **kwargs)
            wildcards=set([permission.split(":")[0]
                           for permission in permissions
                           if permission.endswith(":*")])
            return [permission for permission in permissions
                    if (permission.endswith(":*") or
                        permission.split(":")[0] not in wildcards)]
        return wrapped
    
    @wildcard_override
    def policy_permissions(self, worker,
                           defaults = ["logs:CreateLogGroup",
                                       "logs:CreateLogStream",
                                       "logs:PutLogEvents"]):
        permissions = set(defaults)
        if "permissions" in worker:
            permissions.update(set(worker["permissions"]))
        return sorted(list(permissions))

"""
- this is a temporary solution only!
"""
    
SlackCode="""import base64, gzip, json, os, urllib.request

# https://colorswall.com/palette/3

Levels={"info":  "#5bc0de",
        "warning": "#f0ad4e",
        "error": "#d9534f"}

def post_webhook(struct, url):
    req = urllib.request.Request(url, method = "POST")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(struct).encode()
    return urllib.request.urlopen(req, data = data).read()

def handler(event, context = None,
            colour = Levels[os.environ["SLACK_LOGGING_LEVEL"]],
            webhookurl = os.environ["SLACK_WEBHOOK_URL"]):
    struct = json.loads(gzip.decompress(base64.b64decode(event["awslogs"]["data"])))
    text = json.dumps(struct)
    struct = {"attachments": [{"text": text,
                               "color": colour}]}
    post_webhook(struct, webhookurl)
"""
    
"""
- NB slack-webhook-url defined declaratively / as a Ref, so appears as a top level Parameter
- remember one Slack webhook per application
"""

class SlackFunction(L.InlineFunction):

    def __init__(self, namespace, log_level):
        super().__init__(namespace = namespace,
                         # code = open("/".join(__file__.split("/")[:-1]+["inline_code.py"])).read(),
                         code = SlackCode,
                         variables = {"slack-logging-level": log_level,
                                      "slack-webhook-url": {"Ref": H("slack-webhook-url")}})
    
class SlackLoggingRecipe(Recipe):

    def __init__(self):
        super().__init__()

    """
    - logs are created entirely in the logging namespace
    """
            
    def init_logs(self, parent_ns, log_levels):
        for log_level in log_levels:
            child_ns = f"{parent_ns}-{log_level}"
            self.append(SlackFunction(namespace = child_ns,
                                      log_level = log_level))
            self.append(Role(namespace = child_ns))
            self.append(Policy(namespace = child_ns))
            self.append(L.Permission(namespace = child_ns,
                                                 principal = "logs.amazonaws.com"))

        
