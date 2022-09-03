### continuous deploymnt 03/09/22

- what is you had a cloudformation watcher that watched your code, continually tried to generate a template ?
- then an app which watched for template changes and continually tried to deploy them ?
- feels like inline code is important here so you only have a single artifact
- would this get around the testing problem ? make you feel like you're developing live ?

### component api 03/09/22

- remove local components support
- replace file based iteration with direct imports, renaming init component each time 
- iterate over types and the over individual components
- refactor component classes so you are passing an individual item at a time 
- convert components to classes with render method
- add back support for local components
- flatten component list to remove type containers 

### macro timer 01/09/22

- macro timer which is directly bound to action
- macro timer interval rounds down to 60 seconds
- select macro vs micro based on 1 minute limit

### unified config 01/09/22

- feels like there is value in merging app.props, defaults.yaml, metadata.yaml
- would simplify / clarify things to have stuff in a single place 
- would certainly simplify push artifacts script 
- would probably make it much easier to have stage specific config 
- need to convert all cli scripts fo python from bash 
- could have separate entries for layers for example
- and maybe sns alerts also 

### metadata 27/08/22

- refactor as cloudformation- like structure with (unique) keys for names and types contained inside
- or could be a list
- key is to try and get rid of metadata classes
- can internally contain iterative functions which harvest action refs and check they are consistent etc

### codebuild and action rules 27/08/22

- builder component has its own built- in rule generator, ie it's not a custom thing
- webhook lambda was designed to be used in conjunction with errors lambda
- errors lambda is a destination; pushes messages to eventbridge where they are picked up by webhook lambda
- so is an example of lambda chaining, brokered by eventbridge
- an event bound to the webhook lambda would then want to specify the errors lambda as its source
- but you're not going to get that pattern any more in the new world
- errors lambda will push to sns ie there is no eventbridge event in the middle

### timers and sqs permissions 27/08/22

- some complexity with timers and sqs permissions
- not clear whether timer can invoke demo-target as won't have sqs permissions (as is async)
- should be able to invoke demo-target2 as has sqs permissions, but also has a redundant queue
- which is the better solution?

### action types 26/08/22

- merge queue component into queue type
- queue component to embed sqs iam permissions currently specified in metadata.yaml
- rule binding for async
- async to push errors to sqs, possibly via eventbridge [notes]
- no error handling for apigw
- possible error handling for queue if u can find a model that works
  
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
