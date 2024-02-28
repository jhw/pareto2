### short

AWS::Lambda::Permission:
- pareto2/_components/timer.py
- pareto2/_components/logs.py
- pareto2/_components/topic.py
- pareto2/_components/action/events/__init__.py
- pareto2/_components/api/__init__.py
AWS::Lambda::Function:
- pareto2/_components/queue.py
- pareto2/_components/logs.py
- pareto2/_components/action/__init__.py
- pareto2/_components/table/streaming.py

### medium

AWS::ApiGateway::Authorizer:
- pareto2/_components/api/__init__.py
AWS::ApiGateway::BasePathMapping:
- pareto2/_components/website/domain.py
- pareto2/_components/api/domain.py
AWS::ApiGateway::Deployment:
- pareto2/_components/website/__init__.py
- pareto2/_components/api/cors.py
AWS::ApiGateway::DomainName:
- pareto2/_components/website/domain.py
- pareto2/_components/api/domain.py
AWS::ApiGateway::GatewayResponse:
- pareto2/_components/api/cors.py
AWS::ApiGateway::Method:
- pareto2/_components/website/__init__.py
- pareto2/_components/api/cors.py
- pareto2/_components/api/methods.py
AWS::ApiGateway::Model:
- pareto2/_components/api/validation.py
AWS::ApiGateway::RequestValidator:
- pareto2/_components/api/validation.py
AWS::ApiGateway::Resource:
- pareto2/_components/website/__init__.py
- pareto2/_components/api/__init__.py
AWS::ApiGateway::RestApi:
- pareto2/_components/website/__init__.py
- pareto2/_components/api/__init__.py
AWS::ApiGateway::Stage:
- pareto2/_components/website/__init__.py
- pareto2/_components/api/__init__.py
AWS::Cognito::IdentityPool:
- pareto2/_components/api/userpool.py
AWS::Cognito::IdentityPoolRoleAttachment:
- pareto2/_components/api/userpool.py
AWS::Cognito::UserPool:
- pareto2/_components/api/userpool.py
AWS::Cognito::UserPoolClient:
- pareto2/_components/api/userpool.py
AWS::DynamoDB::Table:
- pareto2/_components/table/__init__.py
AWS::Events::Rule:
- pareto2/_components/timer.py
- pareto2/_components/action/events/__init__.py
AWS::Lambda::EventInvokeConfig:
- pareto2/_components/action/__init__.py
AWS::Lambda::EventSourceMapping:
- pareto2/_components/queue.py
- pareto2/_components/table/streaming.py
AWS::Logs::LogGroup:
- pareto2/_components/action/logs.py
AWS::Logs::LogStream:
- pareto2/_components/action/logs.py
AWS::Logs::SubscriptionFilter:
- pareto2/_components/action/logs.py
AWS::Route53::RecordSet:
- pareto2/_components/website/domain.py
- pareto2/_components/api/domain.py
AWS::S3::Bucket:
- pareto2/_components/bucket.py
- pareto2/_components/website/__init__.py
AWS::SNS::Topic:
- pareto2/_components/topic.py
AWS::SNS::TopicPolicy:
- pareto2/_components/topic.py
AWS::SQS::Queue:
- pareto2/_components/queue.py

### done

AWS::IAM::Role:
- pareto2/_components/queue.py
- pareto2/_components/logs.py
- pareto2/_components/website/__init__.py
- pareto2/_components/action/__init__.py
- pareto2/_components/table/streaming.py
- pareto2/_components/api/userpool.py