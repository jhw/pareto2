from pareto2.aws.apigateway import Deployment as DeploymentBase
from pareto2.aws.apigateway import Method as MethodBase
from pareto2.aws.apigateway import Rssource as ResourceBase
from pareto2.aws.apigateway import Stage as StageBase
from pareto2.aws.iam import Role as RoleBase
from pareto2.aws.s3 import Bucket as BucketBase

class Bucket(BucketBase):

    def __init__(self, website):
        super().__init__(website["name"], "website")

class Role(RoleBase):

    def __init__(self, website, permissions=None):
        super().__init__(website["name"],
                         permissions or ["s3:GetObject"])
        self.service = "apigateway.amazonaws.com"

    def aws_properties(self):
        props = super().aws_properties
        props["AssumeRolePolicyDocument"] = self._assume_role_policy_document(self.service)
        return props

class Resource(ResourceBase):

    def __init__(self, website, pathpart="{proxy+}"):
        super().__init__(website["name"], f"{website['name']}-website-rest-api", pathpart)

    
class Deployment(DeploymentBase):

    def __init__(self, website):
        super().__init__(website["name"])
        self.website = website

    @property
    def aws_properties(self):
        return {
            "RestApiId": {"Ref": f"{self.name}-website-rest-api"},
            "Description": f"created at {int(time.time()*1000)}"
        }

    @property
    def depends(self):
        return [f"{self.name}-website-method"]

class Stage(StageBase):

    def __init__(self, website, stagename="StageName"):
        super().__init__(website["name"], stagename, f"{website['name']}-website-deployment", f"{website['name']}-website-rest-api")

    
class Method(MethodBase):

    def __init__(self, website, **kwargs):
        super().__init__(website["name"], **kwargs)
        self.website = website

    @property
    def aws_properties(self):
        uri = {"Fn::Sub": "arn:aws:apigateway:${AWS::Region}:s3:path/${%s}/{proxy}" % self.website["name"]}
        creds = {"Fn::GetAtt": [f"{self.website['name']}-website-role", "Arn"]}
        reqparams = {"integration.request.path.proxy": "method.request.path.proxy"}
        responses = [
            {"StatusCode": 200, "ResponseParameters": {"method.response.header.Content-Type": "integration.response.header.Content-Type"}},
            {"StatusCode": 404, "SelectionPattern": "404"}
        ]
        integration = {
            "IntegrationHttpMethod": "ANY",
            "Type": "AWS",
            "PassthroughBehavior": "WHEN_NO_MATCH",
            "Uri": uri,
            "Credentials": creds,
            "RequestParameters": reqparams,
            "IntegrationResponses": responses
        }
        methodresponses = [
            {"StatusCode": 200, "ResponseParameters": {"method.response.header.Content-Type": True}},
            {"StatusCode": 404}
        ]
        props = {
            "HttpMethod": "GET",
            "AuthorizationType": "NONE",
            "RequestParameters": {"method.request.path.proxy": True},
            "MethodResponses": methodresponses,
            "Integration": integration,
            "ResourceId": {"Ref": f"{self.website['name']}-website-resource"},
            "RestApiId": {"Ref": f"{self.website['name']}-website-rest-api"}
        }
        return props

class RedirectMethod(MethodBase):
    
    def __init__(self, website, **kwargs):
        super().__init__(website["name"], **kwargs)
        self.website = website

    @property
    def aws_properties(self):
        requests = {"application/json": "{\"statusCode\" : 302}"}
        redirecturl = {"Fn::Sub": ["'https://${name}/index.html'", {"name": {"Ref": "domain-name"}}]}
        responses = [
            {"StatusCode": 302, "ResponseTemplates": {"application/json": "{}"}, "ResponseParameters": {"method.response.header.Location": redirecturl}}
        ]
        integration = {
            "Type": "MOCK",
            "RequestTemplates": requests,
            "IntegrationResponses": responses
        }
        methodresponses = [{"StatusCode": 302, "ResponseParameters": {"method.response.header.Location": True}}]
        props = {
            "HttpMethod": "GET",
            "AuthorizationType": "NONE",
            "MethodResponses": methodresponses,
            "Integration": integration,
            "ResourceId": {"Fn::GetAtt": [f"{self.website['name']}-website-rest-api", "RootResourceId"]},
            "RestApiId": {"Ref": f"{self.website['name']}-website-rest-api"}
        }
        return props
