### deployment 14/07/22

```
aws cloudformation create-stack --stack-name pareto2-demo-dev --template-url http://s3.eu-west-1.amazonaws.com/pareto2-demo-artifacts/main-2022-07-13-16-32-23.json --capabilities CAPABILITY_NAMED_IAM
```

### layer management 07/07/22

- how would a layer management app work ?
- would essentially have to abstract the existing layer routines
- database, bucket, api, lambda functions
- api allows you to manage layers
- when a new layer is added to db, calls a lambda function which kicks off the codebuild process 
- when codebuild process is complete, sends an eventbridge message
- this then calls a second lambda which deploys the layer
- assumes that layers can be created / delete using boto
- also assumes layers can export arns which can then be referenced by other applications

### sync/async lambda checks 30/06/22

- sync lambdas are bound to queues or apigw
- async lambda should have an errors function
- pretty sure timers aren't async
- worth checking that each lambda is either bound to a queue or apigw, or has an errors declaration, or possibly neither

### cross references 22/06/22

- event action against action names
- timer action against action names
- endpoint actions against action names
- endpoint userpool against userpool names
- event router against routers
