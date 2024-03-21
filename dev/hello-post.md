Here is an AWS Cloudformation template which puts an HTTP POST endpoint onto a Lambda function using apigateway. I want to convert this to use apigateway2. Please explain to me what changes need to be made.

{
  "Outputs": {
    "AppRestApi": {
      "Value": {
        "Ref": "AppRestApi"
      }
    }
  },
  "Parameters": {
    "CertificateArn": {
      "Type": "String"
    },
    "DomainName": {
      "Type": "String"
    }
  },
  "Resources": {
    "AppBasePathMapping": {
      "DependsOn": [
        "AppDomainName"
      ],
      "Properties": {
        "DomainName": {
          "Ref": "DomainName"
        },
        "RestApiId": {
          "Ref": "AppRestApi"
        },
        "Stage": "prod"
      },
      "Type": "AWS::ApiGateway::BasePathMapping"
    },
    "AppDeployment": {
      "DependsOn": [
        "AppHelloPostPublicLambdaProxyMethod"
      ],
      "Properties": {
        "RestApiId": {
          "Ref": "AppRestApi"
        }
      },
      "Type": "AWS::ApiGateway::Deployment"
    },
    "AppDomainName": {
      "Properties": {
        "CertificateArn": {
          "Ref": "CertificateArn"
        },
        "DomainName": {
          "Ref": "DomainName"
        }
      },
      "Type": "AWS::ApiGateway::DomainName"
    },
    "AppGatewayResponse4xx": {
      "Properties": {
        "ResponseParameters": {
          "gatewayresponse.header.Access-Control-Allow-Headers": "'*'",
          "gatewayresponse.header.Access-Control-Allow-Origin": "'*'"
        },
        "ResponseType": "DEFAULT_4XX",
        "RestApiId": {
          "Ref": "AppRestApi"
        }
      },
      "Type": "AWS::ApiGateway::GatewayResponse"
    },
    "AppGatewayResponse5xx": {
      "Properties": {
        "ResponseParameters": {
          "gatewayresponse.header.Access-Control-Allow-Headers": "'*'",
          "gatewayresponse.header.Access-Control-Allow-Origin": "'*'"
        },
        "ResponseType": "DEFAULT_5XX",
        "RestApiId": {
          "Ref": "AppRestApi"
        }
      },
      "Type": "AWS::ApiGateway::GatewayResponse"
    },
    "AppHelloPostFunction": {
      "Properties": {
        "Code": {
          "ZipFile": "import json\ndef handler(event, context):\n    body=json.loads(event[\"body\"])\n    message=body[\"message\"]\n    return {\"statusCode\": 200,\n            \"headers\": {\"Content-Type\": \"text/plain\",\n                        \"Access-Control-Allow-Origin\": \"*\",\n                        \"Access-Control-Allow-Headers\": \"Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent\",\n                        \"Access-Control-Allow-Methods\": \"OPTIONS,POST\"},\n            \"body\": f\"you sent '{message}' via POST\"}"
        },
        "Handler": "index.handler",
        "MemorySize": 512,
        "Role": {
          "Fn::GetAtt": [
            "AppHelloPostRole",
            "Arn"
          ]
        },
        "Runtime": "python3.10",
        "Timeout": 5
      },
      "Type": "AWS::Lambda::Function"
    },
    "AppHelloPostModel": {
      "Properties": {
        "ContentType": "application/json",
        "Name": "AppHelloPostModel",
        "RestApiId": {
          "Ref": "AppRestApi"
        },
        "Schema": {
          "$schema": "http://json-schema.org/draft-04/schema#",
          "additionalProperties": false,
          "properties": {
            "message": {
              "type": "string"
            }
          },
          "required": [
            "message"
          ],
          "type": "object"
        }
      },
      "Type": "AWS::ApiGateway::Model"
    },
    "AppHelloPostPermission": {
      "Properties": {
        "Action": "lambda:InvokeFunction",
        "FunctionName": {
          "Ref": "AppHelloPostFunction"
        },
        "Principal": "apigateway.amazonaws.com",
        "SourceArn": {
          "Fn::Sub": "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${AppRestApi}/${AppStage}/POST/hello-post"
        }
      },
      "Type": "AWS::Lambda::Permission"
    },
    "AppHelloPostPublicLambdaProxyMethod": {
      "Properties": {
        "AuthorizationType": "NONE",
        "HttpMethod": "POST",
        "Integration": {
          "IntegrationHttpMethod": "POST",
          "Type": "AWS_PROXY",
          "Uri": {
            "Fn::Sub": [
              "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${arn}/invocations",
              {
                "arn": {
                  "Fn::GetAtt": [
                    "AppHelloPostFunction",
                    "Arn"
                  ]
                }
              }
            ]
          }
        },
        "RequestModels": {
          "application/json": "AppHelloPostModel"
        },
        "RequestValidatorId": {
          "Ref": "AppHelloPostSchemaRequestValidator"
        },
        "ResourceId": {
          "Ref": "AppHelloPostResource"
        },
        "RestApiId": {
          "Ref": "AppRestApi"
        }
      },
      "Type": "AWS::ApiGateway::Method"
    },
    "AppHelloPostResource": {
      "Properties": {
        "ParentId": {
          "Fn::GetAtt": [
            "AppRestApi",
            "RootResourceId"
          ]
        },
        "PathPart": "hello-post",
        "RestApiId": {
          "Ref": "AppRestApi"
        }
      },
      "Type": "AWS::ApiGateway::Resource"
    },
    "AppHelloPostRole": {
      "Properties": {
        "AssumeRolePolicyDocument": {
          "Statement": [
            {
              "Action": [
                "sts:AssumeRole"
              ],
              "Effect": "Allow",
              "Principal": {
                "Service": "lambda.amazonaws.com"
              }
            }
          ],
          "Version": "2012-10-17"
        },
        "Policies": [
          {
            "PolicyDocument": {
              "Statement": [
                {
                  "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                  ],
                  "Effect": "Allow",
                  "Resource": "*"
                },
                {
                  "Action": [
                    "s3:GetObject",
                    "s3:PutObject"
                  ],
                  "Effect": "Allow",
                  "Resource": "*"
                }
              ],
              "Version": "2012-10-17"
            },
            "PolicyName": {
              "Fn::Sub": "app-hello-post-role-policy-${AWS::StackName}"
            }
          }
        ]
      },
      "Type": "AWS::IAM::Role"
    },
    "AppHelloPostSchemaRequestValidator": {
      "Properties": {
        "RestApiId": {
          "Ref": "AppRestApi"
        },
        "ValidateRequestBody": true,
        "ValidateRequestParameters": false
      },
      "Type": "AWS::ApiGateway::RequestValidator"
    },
    "AppRecordSet": {
      "Properties": {
        "AliasTarget": {
          "DNSName": {
            "Fn::GetAtt": [
              "AppDomainName",
              "DistributionDomainName"
            ]
          },
          "EvaluateTargetHealth": false,
          "HostedZoneId": {
            "Fn::GetAtt": [
              "AppDomainName",
              "DistributionHostedZoneId"
            ]
          }
        },
        "HostedZoneName": {
          "Fn::Sub": [
            "${prefix}.${suffix}.",
            {
              "prefix": {
                "Fn::Select": [
                  1,
                  {
                    "Fn::Split": [
                      ".",
                      {
                        "Ref": "DomainName"
                      }
                    ]
                  }
                ]
              },
              "suffix": {
                "Fn::Select": [
                  2,
                  {
                    "Fn::Split": [
                      ".",
                      {
                        "Ref": "DomainName"
                      }
                    ]
                  }
                ]
              }
            }
          ]
        },
        "Name": {
          "Ref": "DomainName"
        },
        "Type": "A"
      },
      "Type": "AWS::Route53::RecordSet"
    },
    "AppRestApi": {
      "Properties": {
        "Name": {
          "Fn::Sub": "app-rest-api-${AWS::StackName}"
        }
      },
      "Type": "AWS::ApiGateway::RestApi"
    },
    "AppStage": {
      "Properties": {
        "DeploymentId": {
          "Ref": "AppDeployment"
        },
        "RestApiId": {
          "Ref": "AppRestApi"
        },
        "StageName": "prod"
      },
      "Type": "AWS::ApiGateway::Stage"
    }
  }
}
