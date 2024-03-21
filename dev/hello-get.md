Here is an AWS Cloudformation template which puts an HTTP GET endpoint onto a Lambda function using apigateway. I want to convert this to use apigateway2. Please explain to me what changes need to be made.

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
        "AppHelloGetPublicLambdaProxyMethod"
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
    "AppHelloGetFunction": {
      "Properties": {
        "Code": {
          "ZipFile": "def handler(event, context):\n    message=event[\"queryStringParameters\"][\"message\"]\n    return {\"statusCode\": 200,\n            \"headers\": {\"Content-Type\": \"text/plain\",\n                        \"Access-Control-Allow-Origin\": \"*\",\n                        \"Access-Control-Allow-Headers\": \"Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent\",\n                        \"Access-Control-Allow-Methods\": \"OPTIONS,GET\"},\n            \"body\": f\"you sent '{message}' via GET\"}"
        },
        "Handler": "index.handler",
        "MemorySize": 512,
        "Role": {
          "Fn::GetAtt": [
            "AppHelloGetRole",
            "Arn"
          ]
        },
        "Runtime": "python3.10",
        "Timeout": 5
      },
      "Type": "AWS::Lambda::Function"
    },
    "AppHelloGetParameterRequestValidator": {
      "Properties": {
        "RestApiId": {
          "Ref": "AppRestApi"
        },
        "ValidateRequestBody": false,
        "ValidateRequestParameters": true
      },
      "Type": "AWS::ApiGateway::RequestValidator"
    },
    "AppHelloGetPermission": {
      "Properties": {
        "Action": "lambda:InvokeFunction",
        "FunctionName": {
          "Ref": "AppHelloGetFunction"
        },
        "Principal": "apigateway.amazonaws.com",
        "SourceArn": {
          "Fn::Sub": "arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${AppRestApi}/${AppStage}/GET/hello-get"
        }
      },
      "Type": "AWS::Lambda::Permission"
    },
    "AppHelloGetPublicLambdaProxyMethod": {
      "Properties": {
        "AuthorizationType": "NONE",
        "HttpMethod": "GET",
        "Integration": {
          "IntegrationHttpMethod": "POST",
          "Type": "AWS_PROXY",
          "Uri": {
            "Fn::Sub": [
              "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${arn}/invocations",
              {
                "arn": {
                  "Fn::GetAtt": [
                    "AppHelloGetFunction",
                    "Arn"
                  ]
                }
              }
            ]
          }
        },
        "RequestParameters": {
          "method.request.querystring.message": true
        },
        "RequestValidatorId": {
          "Ref": "AppHelloGetParameterRequestValidator"
        },
        "ResourceId": {
          "Ref": "AppHelloGetResource"
        },
        "RestApiId": {
          "Ref": "AppRestApi"
        }
      },
      "Type": "AWS::ApiGateway::Method"
    },
    "AppHelloGetResource": {
      "Properties": {
        "ParentId": {
          "Fn::GetAtt": [
            "AppRestApi",
            "RootResourceId"
          ]
        },
        "PathPart": "hello-get",
        "RestApiId": {
          "Ref": "AppRestApi"
        }
      },
      "Type": "AWS::ApiGateway::Resource"
    },
    "AppHelloGetRole": {
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
                    "s3:GetObject"
                  ],
                  "Effect": "Allow",
                  "Resource": "*"
                }
              ],
              "Version": "2012-10-17"
            },
            "PolicyName": {
              "Fn::Sub": "app-hello-get-role-policy-${AWS::StackName}"
            }
          }
        ]
      },
      "Type": "AWS::IAM::Role"
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
