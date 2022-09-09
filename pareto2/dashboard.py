from pareto2.components import hungarorise as H

import json, yaml

PageWidth=24

class Widget(list):

    @classmethod
    def initialise(self, type, params):
        def preprocess(text, params):
            for k, v in params.items():
                text=text.replace("{{%s}}" % k, v)
            return yaml.safe_load(text)
        body=open("/".join(__file__.split("/")[:-1])+"/charts/%s.yaml" % type).read()
        return Widget(preprocess(body, params))
    
    def __init__(self, items=[]):
        list.__init__(self, items)

    def render_text(self, resource, widgets, y):
        prefix="".join(["#" for i in range(int(resource["format"][1:]))])
        props={"markdown": "%s %s" % (prefix, resource["value"])}
        widget={"type": "text",
                "x": 0,
                "y": y.value,
                "width": PageWidth,
                "height": resource["height"],
                "properties": props}
        widgets.append(widget)
        y.increment(resource["height"])
        
    def render_charts(self, resource, widgets, y):
        for row in resource["body"]:
            width=int(PageWidth/len(row))
            for i, chart in enumerate(row):                
                widget={"type": "metric",
                        "x": i*width,
                        "y": y.value,
                        "width": width,
                        "height": resource["height"],
                        "properties": chart}
                widgets.append(widget)
            y.increment(resource["height"])
            
    def render(self, y):
        widgets=[]
        for resource in self:
            fn=getattr(self, "render_%s" % resource["type"])
            fn(resource, widgets, y)
        return widgets

class Widgets(list):

    def __init__(self, items=[]):
        list.__init__(self, items)
    
    def render(self):
        class Offset:
            def __init__(self, value=0):
                self.value=value
            def increment(self, value):
                self.value+=value
        widgets, y = [], Offset()
        for row in self:
            widgets+=row.render(y=y)
        return {"widgets": widgets}

"""
- dash names are specified as otherwise it's very hard to see what stage they belong to; dash is your app root; other widgets are not named because they exist and are visible below the root
- params are defined at init_xxx level as some widgets (eg apigw) might need more than resource name (eg stage)
"""

def render_dash(fn):
    def wrapped(md):
        resourcename, dashprefix, widgets = fn(md)
        dashbody={"Fn::Sub": json.dumps(widgets.render())}
        dashname={"Fn::Sub": "${AppName}-%s-dash-${StageName}" % dashprefix}
        props={"DashboardBody":  dashbody,
               "DashboardName": dashname}
        struct={"Type": "AWS::CloudWatch::Dashboard",
                "Properties": props}
        return (resourcename, struct)
    return wrapped

@render_dash
def init_actions(config):
    resourcename=H("%s-dash-actions" % config["globals"]["app-name"])
    widgets=[Widget.initialise("function",
                               {"Title": action["name"],
                                "ResourceName": "${%s}" % H("%s-function" % action["name"])})
                for action in sorted(config["components"].actions,
                                     key=lambda x: x["name"])]    
    return (resourcename, "actions", Widgets(widgets))

"""
def render_resources(config):
    resources=[]
    for fn in [init_actions]:
        resources+=fn(config)
    return dict(resources)
"""

def render_resources(config):
    return dict([fn(config)
                 for fn in [init_actions]])

if __name__=="__main__":
    try:
        from pareto2.dsl import Config
        config=Config.initialise()
        from pareto2.template import Template
        template=Template("dash")        
        template.resources.update(render_resources(config))
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
