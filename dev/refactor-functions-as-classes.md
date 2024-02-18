I am going to show you some Python functions. They have the same return format but different argument signatures. The functions are designed to assist with code generating AWS cloudformation. Each function returns an internal resource name, an aws type and a props dict. You can ignore the @resource decorators. I want you to refactor these functions as a class implementation. You should have a base class which is then extended in a series of subclasses. Each class should have python properties for resource_name, aws_type and aws_props. Values required by the aws_props decorator should be passed as class constructors. The aim is to avoid the duplication which is present in the existing function implementations. For example, as aws_type is the same in each of the functions, only the base class will likely need to implement the aws_type decorator. It's mainly the aws_props decorator which will need to be overloaded. Subclasses may need to call the same properties on the superclass, and then extend them. You can choose whatever names for these different functions you like, but clues as to the usage lie in the comments above each function. You might want to use them. For the base class, use something which reflects the core aws type. PS the function H() hungarorises a string.

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
