from pareto2.core.components import hungarorise as H

import json, yaml

ChartSrc="pareto2/core/charts/%s.yaml"

PageWidth=24

class Component(list):

    @classmethod
    def initialise(self, type, params):
        def preprocess(text, params):
            for k, v in params.items():
                text=text.replace("{{%s}}" % k, v)
            return yaml.safe_load(text)
        body=open(ChartSrc % type).read()
        return Component(preprocess(body, params))
    
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

class Components(list):

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
- dash names are specified as otherwise it's very hard to see what stage they belong to; dash is your app root; other components are not named because they exist and are visible below the root
- params are defined at init_xxx level as some components (eg apigw) might need more than resource name (eg stage)
"""

def render_dash(fn):
    def wrapped(md):
        resourcename, dashprefix, components = fn(md)
        dashbody={"Fn::Sub": json.dumps(components.render())}
        dashname={"Fn::Sub": "${AppName}-%s-dash-${StageName}" % dashprefix}
        props={"DashboardBody":  dashbody,
               "DashboardName": dashname}
        struct={"Type": "AWS::CloudWatch::Dashboard",
                "Properties": props}
        return (resourcename, struct)
    return wrapped

@render_dash
def init_actions(md):
    resourcename=H("%s-dash-actions" % md.dashboard["name"])
    components=[Component.initialise("function",
                                     {"Title": action["name"],
                                      "ResourceName": "${%s}" % H("%s-function" % action["name"])})
                for action in sorted(md.actions,
                                     key=lambda x: x["name"])]
    return (resourcename, "actions", Components(components))

@render_dash
def init_events(md):
    resourcename=H("%s-dash-events" % md.dashboard["name"])
    components=[Component.initialise("event-rule",
                                     {"Title": event["name"],
                                      "ResourceName": "${%s}" % H("%s-event-rule" % event["name"])})
                for event in sorted(md.events,
                                    key=lambda x: x["name"])]
    return (resourcename, "events", Components(components))

@render_dash
def init_timers(md):
    resourcename=H("%s-dash-timers" % md.dashboard["name"])
    components=[Component.initialise("timer-rule",
                                     {"Title": timer["name"],
                                      "ResourceName": "${%s}" % H("%s-timer-rule" % timer["name"])})
                for timer in sorted(md.timers,
                                    key=lambda x: x["name"])]
    return (resourcename, "timers", Components(components))

@render_dash
def init_table(md):
    resourcename=H("%s-dash-table" % md.dashboard["name"])
    components=[Component.initialise("table",
                                     {"Title": table["name"],
                                      "ResourceName": "${%s}" % H("%s-table" % table["name"])})
                for table in sorted(md.tables,
                                    key=lambda x: x["name"])]
    return (resourcename, "table", Components(components))

@render_dash
def init_bucket(md):
    resourcename=H("%s-dash-bucket" % md.dashboard["name"])
    components=[Component.initialise("bucket",
                                     {"Title": bucket["name"],
                                      "ResourceName": "${%s}" % H("%s-bucket" % bucket["name"])})
                for bucket in sorted(md.buckets,
                                     key=lambda x: x["name"])]
    return (resourcename, "bucket", Components(components))

@render_dash
def init_api(md):
    resourcename=H("%s-dash-api" % md.dashboard["name"])
    components=[Component.initialise("api",
                                     {"Title": api["name"],
                                      "ResourceName": "${%s}" % H("%s-api-rest-api" % api["name"])})
                for api in sorted(md.apis,
                                  key=lambda x: x["name"])]
    return (resourcename, "api", Components(components))

def init_resources(md):
    return dict([fn(md)
                 for fn in [init_actions,
                            init_events,
                            init_timers,
                            init_table,
                            init_bucket,
                            init_api]])

def update_template(template, md):
    template.resources.update(init_resources(md))

if __name__=="__main__":
    try:
        from pareto2.core.template import Template
        template=Template("dashboards")
        from pareto2.core.metadata import Metadata
        md=Metadata.initialise()
        md.validate().expand()
        update_template(template, md)
        template.dump_local()
    except RuntimeError as error:
        print ("Error: %s" % str(error))
