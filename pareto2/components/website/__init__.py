from pareto2.components import hungarorise as H
from pareto2.components import resource

from pareto2.components.website.domain import init_domain, init_domain_path_mapping, init_domain_record_set

from pareto2.components.common.iam import policy_document, assume_role_policy_document

StageName="prod"

@resource
def init_rest_api(website):
    resourcename=H("%s-website-rest-api" % website["name"])
    name={"Fn::Sub": "%s-website-rest-api-${AWS::StackName}" % website["name"]}
    props={"Name": name}
    return (resourcename,            
            "AWS::ApiGateway::RestApi",
            props)

@resource
def init_deployment(website):
    resourcename=H("%s-website-deployment" % website["name"])
    props={"RestApiId": {"Ref": H("%s-website-rest-api" % website["name"])}}
    depends=[H("%s-website-method" % endpoint["name"])]
    return (resourcename,            
            "AWS::ApiGateway::Deployment",
            props,
            depends)

@resource
def init_stage(website, stagename=StageName):
    resourcename=H("%s-website-stage" % website["name"])
    props={"StageName": stagename,
           "DeploymentId": {"Ref": H("%s-website-deployment" % website["name"])},
           "RestApiId": {"Ref": H("%s-website-rest-api" % website["name"])}}
    return (resourcename,
            "AWS::ApiGateway::Stage",
            props)

@resource
def init_resource(website, pathpart="{proxy+}"):
    resourcename=H("%s-website-resource" % website["name"])
    parentid={"Fn::GetAtt": [H("%s-website-rest-api" % website["name"]),
                             "RootResourceId"]}
    props={"ParentId": parentid,
           "PathPart": pathpart,
           "RestApiId": {"Ref": H("%s-website-rest-api" % website["name"])}}
    return (resourcename,
            "AWS::ApiGateway::Resource",
            props)
@resource
def init_role(website,
              permissions=["s3:GetObject"]):
    resourcename=H("%s-website-role" % website["name"])
    policyname={"Fn::Sub": "%s-website-role-policy-${AWS::StackName}" % website["name"]}
    policyresource={"Fn::Sub": "arn:aws:s3:::${S3Bucket}/*"  % H("%s-website" % website["name"])}
    policydoc=policy_document(permissions, resource=policyresource)
    policies=[{"PolicyDocument": policydoc,
               "PolicyName": policyname}]
    props={"AssumeRolePolicyDocument": assume_role_policy_document(service="apigateway.amazonaws.com"),
           "Policies": policies}
    return (resourcename,
            "AWS::IAM::Role",
            props)

@resource
def init_method(website):
    resourcename=H("%s-website-method" % website["name"])
    uri={"Fn::Sub": "arn:aws:apigateway:${AWS::Region}:s3:path/${%s}/{proxy}" % H("%s-website" % website["name"])}
    credentials={"Fn::GetAtt": [H("%s-website-role" % website["name"]),
                                "Arn"]}
    requestparams={"integration.request.path.proxy": "method.request.path.proxy"}
    integration={"IntegrationHttpMethod": "ANY",
                 "Type": "AWS",
                 "PassthroughBehaviour": "WHEN_NO_MATCH",
                 "Uri": uri,
                 "Credentials": credentials,
                 "RequestParameters": requestparams, 
                 "IntegrationResponses": [{"StatusCode": 200}]}
    props={"HttpMethod": "GET",
           "AuthorizationType": "NONE",
           "RequestParameters": {"method.request.path.proxy": True},
           "MethodResponses": [{"StatusCode": 200}],
           "Integration": integration,
           "ResourceId": {"Ref": H("%s-website-resource" % website["name"])},
           "RestApiId": {"Ref": H("%s-website-rest-api" % website["name"])}}
    return (resourcename,
            "AWS::ApiGateway::Method",
            props)

@resource
def init_bucket(website):
    resourcename=H("%s-website" % website["name"])
    notconf={"EventBridgeConfiguration": {"EventBridgeEnabled": True}}
    props={"NotificationConfiguration": notconf}
    return (resourcename,
            "AWS::S3::Bucket",
            props)

def render_resources(website):
    resources=[]
    for fn in [init_bucket,
               init_rest_api,
               init_deployment,
               init_stage,
               init_resource,
               init_role,
               init_method,
               init_bucket,
               init_domain,
               init_domain_path_mapping,
               init_domain_record_set]:
        resource=fn(website)
        resources.append(resource)
    return dict(resources)

def render_outputs(website):
    return {H("%s-website" % website["name"]): {"Value": {"Ref": H("%s-website" % website["name"])}}}

if __name__=="__main__":
    pass
