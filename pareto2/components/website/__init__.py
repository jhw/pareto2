from pareto2.components import hungarorise as H
from pareto2.components import resource

from pareto2.components.website.domain import init_domain, init_domain_path_mapping, init_domain_record_set

from pareto2.components.common.iam import policy_document, assume_role_policy_document

import yaml

BinaryMediaTypes=yaml.safe_load("""
- audio/mpeg
- image/jpeg
- image/x-png
""")

StageName="prod"

@resource
def init_rest_api(website, binarymediatypes=BinaryMediaTypes):
    resourcename=H("%s-website-rest-api" % website["name"])
    name={"Fn::Sub": "%s-website-rest-api-${AWS::StackName}" % website["name"]}
    props={"Name": name,
           "BinaryMediaTypes": binarymediatypes}
    return (resourcename,            
            "AWS::ApiGateway::RestApi",
            props)

@resource
def init_deployment(website):
    resourcename=H("%s-website-deployment" % website["name"])
    props={"RestApiId": {"Ref": H("%s-website-rest-api" % website["name"])}}
    depends=[H("%s-website-method" % website["name"])]
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
    policyresource={"Fn::Sub": "arn:aws:s3:::${%s}/*"  % H("%s-website" % website["name"])}
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
    def init_integration(website):
        uri={"Fn::Sub": "arn:aws:apigateway:${AWS::Region}:s3:path/${%s}/{proxy}" % H("%s-website" % website["name"])}
        creds={"Fn::GetAtt": [H("%s-website-role" % website["name"]),
                              "Arn"]}
        reqparams={"integration.request.path.proxy": "method.request.path.proxy"}
        responses=[{"StatusCode": 200,
                    "ResponseParameters": {"method.response.header.Content-Type": "integration.response.header.Content-Type"}},
                   {"StatusCode": 404,
                    "SelectionPattern": "404"}]
        return {"IntegrationHttpMethod": "ANY",
                "Type": "AWS",
                "PassthroughBehavior": "WHEN_NO_MATCH",
                "Uri": uri,
                "Credentials": creds,
                "RequestParameters": reqparams, 
                "IntegrationResponses": responses}        
    resourcename=H("%s-website-method" % website["name"])
    integration=init_integration(website)
    reqparams={"method.request.path.proxy": True}
    methodresponses=[{"StatusCode": 200,
                      "ResponseParameters": {"method.response.header.Content-Type": True}},
                     {"StatusCode": 404}]
    props={"HttpMethod": "GET",
           "AuthorizationType": "NONE",
           "RequestParameters": reqparams,
           "MethodResponses": methodresponses,
           "Integration": integration,
           "ResourceId": {"Ref": H("%s-website-resource" % website["name"])},
           "RestApiId": {"Ref": H("%s-website-rest-api" % website["name"])}}
    return (resourcename,
            "AWS::ApiGateway::Method",
            props)

@resource
def init_root_redirect_method(website):
    def init_integration(website):
        requests={"application/json": "{\"statusCode\" : 302}"}
        redirecturl={"Fn::Sub": ["'https://${prefix}.${name}/index.html'", # NB note single quotes
                                 {"prefix": {"Ref": H("%s-website-domain-prefix" % website["name"])},
                                  "name": {"Ref": H("domain-name")}}]}
        responses=[{"StatusCode": 302,
                    "ResponseTemplates": {"application/json": "{}"},
                    "ResponseParameters": {"method.response.header.Location": redirecturl}}]
        return {"Type": "MOCK",
                "RequestTemplates": requests,
                "IntegrationResponses": responses}        
    resourcename=H("%s-website-root-redirect-method" % website["name"])
    integration=init_integration(website)
    methodresponses=[{"StatusCode": 302,
                      "ResponseParameters": {"method.response.header.Location": True}}]
    parentid={"Fn::GetAtt": [H("%s-website-rest-api" % website["name"]),
                             "RootResourceId"]}
    props={"HttpMethod": "GET",
           "AuthorizationType": "NONE",
           "MethodResponses": methodresponses,
           "Integration": integration,
           "ResourceId": parentid, 
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
               init_root_redirect_method,
               init_bucket,
               init_domain,
               init_domain_path_mapping,
               init_domain_record_set]:
        resource=fn(website)
        resources.append(resource)
    return dict(resources)

"""
- RestApi and Stage (echoed from input) are required for apigw redeployment
"""

def render_outputs(website):
    bucket={"Ref": H("%s-website" % website["name"])}
    restapi={"Ref": H("%s-website-rest-api" % website["name"])}
    stage={"Ref": H("%s-website-stage" % website["name"])}
    dnsname={"Fn::GetAtt": [H("%s-website-domain" % website["name"]), "DistributionDomainName"]}
    hzid={"Fn::GetAtt": [H("%s-website-domain" % website["name"]), "DistributionHostedZoneId"]}
    outputs={}
    for k, v in {"website": bucket,
                 "website-rest-api": restapi,
                 "website-stage": stage,
                 "website-dns-name": dnsname,
                 "website-hosted-zone-id": hzid}.items():
        outputs[H("%s-%s" % (website["name"], k))]={"Value": v}
    return outputs

if __name__=="__main__":
    pass
