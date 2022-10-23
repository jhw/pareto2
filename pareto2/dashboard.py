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

def render_dash(fn):
    def wrapped(md):
        resourcename, dashprefix, widgets = fn(md)
        dashbody={"Fn::Sub": json.dumps(widgets.render())}
        props={"DashboardBody":  dashbody,
               "DashboardName": dashprefix}
        struct={"Type": "AWS::CloudWatch::Dashboard",
                "Properties": props}
        return (resourcename, struct)
    return wrapped

@render_dash
def init_actions(config):
    resourcename=H("dash-actions")
    widgets=[Widget.initialise("function",
                               {"Title": action["name"],
                                "ResourceName": "${%s}" % H("%s-function" % action["name"])})
                for action in sorted(config["components"].actions,
                                     key=lambda x: x["name"])]    
    return (resourcename, "actions", Widgets(widgets))

@render_dash
def init_buckets(config):
    resourcename=H("dash-buckets")
    widgets=[Widget.initialise("function",
                               {"Title": bucket["name"],
                                "ResourceName": "${%s}" % H("%s-bucket" % bucket["name"])})
                for bucket in sorted(config["components"].buckets,
                                     key=lambda x: x["name"])]    
    return (resourcename, "buckets", Widgets(widgets))

@render_dash
def init_tables(config):
    resourcename=H("dash-tables")
    widgets=[Widget.initialise("function",
                               {"Title": table["name"],
                                "ResourceName": "${%s}" % H("%s-table" % table["name"])})
                for table in sorted(config["components"].tables,
                                     key=lambda x: x["name"])]    
    return (resourcename, "tables", Widgets(widgets))

def render_resources(config):
    return dict([fn(config)
                 for fn in [init_actions,
                            init_buckets,
                            init_tables]])

if __name__=="__main__":
    try:
        import os, sys
        filename=sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
        if not os.path.exists(filename):
            raise RuntimeError("%s does not exist" % filename)
        from pareto2.dsl import Config
        config=Config.init_file(filename=filename)
        from pareto2.template import Template
        template=Template()        
        template.resources.update(render_resources(config))
        print (template.render())
    except RuntimeError as error:
        print ("Error: %s" % str(error))
