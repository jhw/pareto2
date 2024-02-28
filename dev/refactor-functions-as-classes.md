I am going to show you some Python functions which take different arguments but return the same structure. I want you to convert them to a class implementation in which the three outputs from each function are replaced by properties for resource_name (string), aws_resource_type (string) and aws_properties (dict). You should create a base class which encapsulates the common parts of these functions. The base class name should reflect the aws_type, particularly the final slug; so a base class which returns AWS::Lambda::Function should be called FunctionBase. Arguments to the functions should be replaced by constructor arguments and saved as instance variables, so that they can be referenced by the property functions. The base class should have default values for every argument. You should create a subclass for each of the functions shown, whose constructor signatures match the function argument signatures. Subclass names should reflect the names in comments above the function body (ignoring pareto, components and __init___ slugs) and the names of the original functions (ignoring init slug). Please maintain these comments above the new class bodies. Each of the functions has the same aws_type, so you will only need an aws_type property in the base class.  All the complexity here is in the aws_properties property. Please return a full code listing that can be copied and pasted and work immediately.

--

# pareto2/components/queue.py

@resource
def init_dlq_function_role(queue,
                           permissions=["logs:CreateLogGroup",
                                        "logs:CreateLogStream",
                                        "logs:PutLogEvents",
                                        "sqs:DeleteMessage",
                                        "sqs:GetQueueAttributes",
                                        "sqs:ReceiveMessage"]):
    resourcename=H("%s-queue-dlq-function-role" % queue["name"])
    policyname={"Fn::Sub": "%s-queue-dlq-function-role-policy-${AWS::StackName}" % queue["name"]}
    policydoc=policy_document(permissions)
    policies=[{"PolicyDocument": policydoc,
               "PolicyName": policyname}]
    props={"AssumeRolePolicyDocument": assume_role_policy_document(),
           "Policies": policies}
    return (resourcename,
            "AWS::IAM::Role",
            props)

# pareto2/components/logs.py

@resource
def init_function_role(logs,
                       permissions=["logs:CreateLogGroup",
                                    "logs:CreateLogStream",
                                    "logs:PutLogEvents"]):
    resourcename=H("%s-logs-function-role" % logs["name"])
    policyname={"Fn::Sub": "%s-logs-function-role-policy-${AWS::StackName}" % logs["name"]}
    policydoc=policy_document(permissions)
    policies=[{"PolicyDocument": policydoc,
               "PolicyName": policyname}]
    props={"AssumeRolePolicyDocument": assume_role_policy_document(),
           "Policies": policies}
    return (resourcename,
            "AWS::IAM::Role",
            props)

# pareto2/components/website/__init__.py

@resource
def init_role(website,
              permissions=["s3:GetObject"]):
    resourcename=H("%s-website-role" % website["name"])
    policyname={"Fn::Sub": "%s-website-role-policy-${AWS::StackName}" % website["name"]}
    policyresource={"Fn::Sub": "arn:aws:s3:::${%s}/*"  % H("%s-website" % website["name"])}
    policydoc=policy_document(permissions, resource=policyresource)
    policies=[{"PolicyDocument": policydoc,
               "PolicyName": policyname}]
    props={"AssumeRolePolicyDocument": assume_role_policy_document(service="apigateway.amazonaws.com"),
           "Policies": policies}
    return (resourcename,
            "AWS::IAM::Role",
            props)

# pareto2/components/action/__init__.py

@resource
def init_function_role(action, basepermissions=BasePermissions):
    def init_permissions(action, basepermissions):
        permissions=set(basepermissions)
        if "permissions" in action:
            permissions.update(set(action["permissions"]))
        return sorted(list(permissions))
    resourcename=H("%s-function-role" % action["name"])
    policyname={"Fn::Sub": "%s-function-role-policy-${AWS::StackName}" % action["name"]}
    policydoc=policy_document(init_permissions(action, basepermissions))
    policies=[{"PolicyDocument": policydoc,
               "PolicyName": policyname}]
    props={"AssumeRolePolicyDocument": assume_role_policy_document(),
           "Policies": policies}
    return (resourcename,
            "AWS::IAM::Role",
            props)

# pareto2/components/table/streaming.py

@resource
def init_streaming_role(table,
                        permissions=["dynamodb:GetRecords",
                                     "dynamodb:GetShardIterator",
                                     "dynamodb:DescribeStream",
                                     "dynamodb:ListStreams",
                                     "events:PutEvents",
                                     "logs:CreateLogGroup",
                                     "logs:CreateLogStream",
                                     "logs:PutLogEvents"]):
    resourcename=H("%s-table-streaming-function-role" % table["name"])
    policyname={"Fn::Sub": "%s-table-streaming-function-role-policy-${AWS::StackName}" % table["name"]}
    policydoc=policy_document(permissions)
    policies=[{"PolicyDocument": policydoc,
               "PolicyName": policyname}]
    props={"AssumeRolePolicyDocument": assume_role_policy_document(),
           "Policies": policies}
    return (resourcename,
            "AWS::IAM::Role",
            props)

# pareto2/components/api/userpool.py

@resource
def init_identitypool_unauthorized_role(api,
                                        permissions=["mobileanalytics:PutEvents",
                                                     "cognito-sync:*"]):
    resourcename=H("%s-api-identitypool-unauthorized-role" % api["name"])
    assumerolepolicydoc=role_policy_document(api, "unauthenticated")
    policyname=H("%s-api-identitypool-unauthorized-role-policy" % api["name"])
    policydoc=policy_document(permissions)
    policy={"PolicyName": policyname,
            "PolicyDocument": policydoc}
    props={"AssumeRolePolicyDocument": assumerolepolicydoc,
           "Policies": [policy]}
    return (resourcename, 
            "AWS::IAM::Role",
            props)

# pareto2/components/api/userpool.py

@resource
def init_identitypool_authorized_role(api,
                                      permissions=["mobileanalytics:PutEvents",
                                                   "cognito-sync:*",
                                                   "cognito-identity:*",
                                                   "lambda:InvokeFunction"]):
    resourcename=H("%s-api-identitypool-authorized-role" % api["name"])
    assumerolepolicydoc=role_policy_document(api, "authenticated")
    policyname=H("%s-api-identitypool-authorized-role-policy" % api["name"])
    policydoc=policy_document(permissions)
    policy={"PolicyName": policyname,
            "PolicyDocument": policydoc}
    props={"AssumeRolePolicyDocument": assumerolepolicydoc,
           "Policies": [policy]}
    return (resourcename, 
            "AWS::IAM::Role",
            props)
