I am going to show you some Python function. They all return the same structure. I want you to convert them to a class implementation in which the three outputs from each function are replaced by properties for resource_name (an internal string name), aws_type (the aws resource type; a string) and aws_properties (the aws properties; a dict). You should create a base class which encapsulates the common parts of these functions. Arguments to the functions should be replaced by contructor arguments which are saved as instance variables, which can then be referenced from the properties, particularly aws_properties. The base class should have default values for every argument. There should then be a subclass for each of the functions show, which constructor signatures that match the function argument signatures. Please return all code. 

--

# aws/lambda/function

@resource            
def init_dlq_function(queue,
                      size=SlackSize,
                      timeout=SlackTimeout,
                      envvars=["slack-webhook-url"],
                      code=SlackFunctionCode):
    resourcename=H("%s-queue-dlq-function" % queue["name"])
    rolename=H("%s-queue-dlq-function-role" % queue["name"])
    code={"ZipFile": code}
    runtime={"Fn::Sub": "python${%s}" % H("runtime-version")}
    memorysize=H("memory-size-%s" % size)
    timeout=H("timeout-%s" % timeout)
    variables={U(k): {"Ref": H(k)}
               for k in envvars}
    props={"Role": {"Fn::GetAtt": [rolename, "Arn"]},
           "MemorySize": {"Ref": memorysize},
           "Timeout": {"Ref": timeout},
           "Code": code,
           "Handler": "index.handler",
           "Runtime": runtime,
           "Environment": {"Variables": variables}}
    return (resourcename, 
            "AWS::Lambda::Function",
            props)

# aws/lambda/function

@resource            
def init_function(logs,
                  code=SlackFunctionCode):
    resourcename=H("%s-logs-function" % logs["name"])
    rolename=H("%s-logs-function-role" % logs["name"])
    code={"ZipFile": code}
    runtime={"Fn::Sub": "python${%s}" % H("runtime-version")}
    memorysize=H("memory-size-%s" % logs["function"]["size"])
    timeout=H("timeout-%s" % logs["function"]["timeout"])
    variables={U("slack-webhook-url"): {"Ref": H("slack-webhook-url")},
               U("slack-logging-level"): logs["level"]}
    props={"Role": {"Fn::GetAtt": [rolename, "Arn"]},
           "MemorySize": {"Ref": memorysize},
           "Timeout": {"Ref": timeout},
           "Code": code,
           "Handler": "index.handler",
           "Runtime": runtime,
           "Environment": {"Variables": variables}}
    return (resourcename, 
            "AWS::Lambda::Function",
            props)

# aws/lambda/function

@resource            
def init_function(action):    
    resourcename=H("%s-function" % action["name"])
    rolename=H("%s-function-role" % action["name"])
    memorysize=H("memory-size-%s" % action["size"])
    timeout=H("timeout-%s" % action["timeout"])
    code={"S3Bucket": {"Ref": H("artifacts-bucket")},
          "S3Key": {"Ref": H("artifacts-key")}}
    handler={"Fn::Sub": "%s/index.handler" % action["path"].replace("-", "/")}
    runtime={"Fn::Sub": "python${%s}" % H("runtime-version")}
    props={"Role": {"Fn::GetAtt": [rolename, "Arn"]},
           "MemorySize": {"Ref": memorysize},
           "Timeout": {"Ref": timeout},
           "Code": code,
           "Handler": handler,
           "Runtime": runtime}
    if "layers" in action:
        props["Layers"]=[{"Ref": H("%s-layer-arn" % pkgname)}
                         for pkgname in action["layers"]]
    if "env" in action:
        variables={U(k): {"Ref": H(k)}
                   for k in action["env"]["variables"]}
        props["Environment"]={"Variables": variables}
    return (resourcename, 
            "AWS::Lambda::Function",
            props)
