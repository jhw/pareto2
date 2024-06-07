### cognito callbacks 07/06/24

- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-cognito-userpool-lambdaconfig.html

### migrations script 08/04/24

- rename API as paas 
- load assets as per API init 
- iterate through handlers
- determine what each handler is
- event, endpoint, topic, queue, timer.
- reformat triggers for non- endpoint stuff into events
- remove names
- remove names related to event types 
- convert sizes and timeouts to integers
- pass through permissions and layers
- add alarm to worker
- remove endpoint post schema 
- maintain list of endpoint public / private Auth levels
- maintain a list of dB indexes
- refactor table name, bucket name refs 
- refactor old long queue names 
- dump entire tree to tmp

### manifesto 08/04/24

- why write your own framework.
- smart people told me not to but I went ahead anyway 
- the thing is I think this space is important but very young
- witness the number of frameworks around
- severless, sst, wing, ampt, begin, amplify 
- it's a bit like blogging circa 2023
- writing you own paas framework a bit like writing your own blogging engine
- sst get the closest but still not quite there
- write your own because you don't want to find yourself in a vercel like situation 

---

- you can build amazing apps with serverless but it's about much more than lambda
- you have to stitch multiple services together to make it sing
- lambda, S3, dynamodb, eventbridge, sqs, sns, IAM cognito
- a big aspect of serverless is pushing as much stuff into the infrastructure as possible 
- the problem is the skills you need to do this are very different from coding apps in python or JavaScript
- because the medium - Cloudformation - is so different 

---

- it's declarative and it's extremely verbose 
- certainly if you're coding it by hand there is a big problem
- there are so many places to trip you up
- refs and IDs and arns for starters
- the ubiquity of IAM 
- the craziness of API gateway and cognito 
- all multiplied by the slowness of Cloudformation 
- it's a mess

---

- however it's very powerful
- and you can argue you only need a few patterns done well
- what you need is a layer above it to manage it for you 
- something to embody the patterns
- something to manage the namespacing
- something to wrap the craziness

---

- so what are these patterns
- firstly you what a robust http api obviously 
- you want blob and row storage 
- you want notifications and data streaming so you don't have to poll
- you want timer and delay capabilities 
- and you want observability and alerting baked in
- you want to be able to access all this from a minimal amount of config, and something close to the code

--

- what comes out of this is the importance of workers
- all paas you an http api, much fewer give you good offline processing capabilities 
- hat tip google app engine
- workers being pinged by timers, workers being handed queue jobs, worker responding to notifications 
- it's nice to have a single catch all pattern here
- in Aws you have a lot of messaging options 
- sns, sws, eventbridge, Kafka and kinesis
- settle on Eventbridge as most versatile 
- because of decentralised structure 
- anything which doesn't natively speak eventbridge, put an inline lambda in front of it which does conversion 
- S3 does but sqs and dynamodb don't 
- wrapping them in this way means the mechanics of sync invocations and lookback permissions can be baked into the stack and hidden from the app devs

---

- ci/cd is hugely important here
- the standard cd pipeline just wraps whatever crap you have in docker and throws it into production
- you can't do that here because you have an all important infrastructure building step
- and the cd pipeline is a great place to run that 
- so your cd pipeline has to become opionated 
- it will build you app and push to production, but only if your app follows certain standards
- that means more than just adhering to a particular framework (so the pipeline knows how to build)
- you could / should be running unit tests as part of ci/cd
- and you could also have your pipeline strip out, store and version app documentation
- no docs? No deployment!
- so imagine your cd pipeline as less of a postman and more of a policeman 
- and think of your framework and cd pipeline as partners 

---

- and what of the binding layer?
- this is where is becomes tricky
- writing biz logic and defining infra are very different propositions, hence pareto
- but you still need infra snippets which the framework can expand from
- where should they go?
- want to stay close to the code
- but complex because some bits of infra are handler specific whilst some are app level.
- settle on yaml fragments within code
- but should maybe think of python annotations asa better solution
- ultimately some combined solution like wing?

### Name fields 08/04/24

- AWS::Events::Rule Target Id
- AWS::IAM::Policy PolicyName
- AWS::ApiGatewayV2::Api Name

- first is defined as "within the rule" so is clearly local; AWS::StackName can be removed, which is a good thing as there is a 64 character limit here
- the latter two area required, but it's not clear what the namespacing is; they don't appear to be "contained" by anything other than the stack itself; hence feels best to probably include AWS::StackName in the name, just in case you want more than one similar stack on a particular account

### bindings 05/04/24

- two aspects, root and lambda
- root could be defining in app/__init__.py or separate yaml file in app root
- think the former better as consistent with current lambda handling
- use dsl script parsing code from pareto 0.7
- root defines bucket, table, queue, api, builder
- presence of each determines whether recipe is included in app recipe
- root values are dicts
- website is determined by bucket public = true
- some limited checking such as can't have an API and a public bucket 
- anything in the above list is created in the app workspace 
- have a main recipe and then add sub recipes to it before creating template 
- then a handler should be much simplified 
- is either a worker or a timer or an api endpoint 
- that's it
- validate and add relevant recipe
- note that api needs to be created first and then endpoints later
- also how to name worker and timer namespaces
- remember endpoint is named after path
- but timer and worker need their own name fields
- worker event should have a type field which leads to insertion of source into app pattern 
- or project name in the case of builder
- should also have an unbound or public option 
- and any environment variables must be filtered from the handler and added as iac environment variables

### optimiser 04/04/24

- so you could have something which looked for very specific patterns and tried to optimise them, before a recipe is rendered to a template
- a good example would be Role
- they are almost always the same, save for some Cognito specific stuff
- filter roles from resources
- group logical ids by type where key is JSON.dumps(resource["Properties"], sort_keys=True)
- ignore any unique keys
- generate new optimiser roles from first item in each non- unique key set
- create map of old to new references
- iterate through structure and replace old with new
- remove old roles and add new optimised ones

### micro timer 03/04/24

- subsecond timer in addition to usual down-to-one-minute timer?
- think is you can easily construct this from event timer and task queue
- just have timer push items to queue, which are then pushed to eventbridge
- only extra bit of glue you need is lambda to do the pushing
- any "baked in" subsecond timer is just going to repeat this pattern
- should task queue then be subclassed within recipes?
- should subsecond tasks be executed via lambda.invoke, or via eventbridge?
- neither of these seem like profitable or sensible questions to ask
- therefore leave a subsecond timer out of the PaaS API for the minute, but allow users to construct one from the core components

### dsl 02/04/24

- load bucket, table, api, website, queue, pip builder config from root
  - can't have api and website
  - website uses bucket- 
- load handlers from lambda
- handler type field
  - endpoint, worker, timer

### expander2 01/04/24

- remove redeployer
- handler type field
  - endpoint, worker, timer
- worker event-type field
  - bucket, table, queue, project
  - inserts relevant source or project-type field into pattern
- templater to check certificate region
  - default region for web-api
  - us-east-1 for website

### builder 30/03/24

- codebuild package with Project
- S3Project to extend Project and include all S3 rubbish
- skeleton pip builder recipe
- incude buildspec.yaml in recipe
- create project and role
- demo to dump template
- demo to include worker which targets codebuild notifications
- include Project ref in event definition
- worker to push messages to slack
- gist to test everything

### sns to slack 25/03/24

- proposal is to send notifications to sns, along with level, and have a single slack handler which sends to slack
- but not sure this makes a lot of sense
- you already have a method of indirection facilitated by cloudwatch and the subscription filters
- these are effectively taking the role of sns
- just logging.warn() instead of sending to sns
- yes you have two slack handlers with duplicate slack code
- but you'll never need more than that
- eg alarm code just needs to logging.warn() and the existing handlers will pick it up
- so you can see in this way that cloudwatch is effectively a notification system

### apigatewayV2 21/03/24

- Replace AWS::ApiGateway::RestApi with AWS::ApiGatewayV2::Api.
- Replace AWS::ApiGateway::Stage with AWS::ApiGatewayV2::Stage.
- Replace AWS::ApiGateway::BasePathMapping with AWS::ApiGatewayV2::ApiMapping.
- Replace AWS::ApiGateway::Method with AWS::ApiGatewayV2::Route.
- Replace AWS::ApiGateway::Deployment with AWS::ApiGatewayV2::Deployment.

- methods replaced by routes and integrations
- domain name has an endpoint type
- validation looks to be the same 
- cors is an integration

### events 17/03/24

- i start to think the existing pareto events paradigm is an antipattern
- particularly the way the bindings to internal table and bucket are done
- because it then seems to necessitate subclasses with different source bindings
- which doesn't feel good.n a pareto 7 world 
- it feels like it might be better to have a single events class for now in which the client has to specify the raw event payload
- detail, detail type, source and all 
- remember you may need multiple events per worker
- so each event needs a name and must live in a child namespace
- the function/event relationship is very like the API/endpoint relationship 
- this in turn should make things easier to test
- because you don't have bindings
- so you could define a worker which simply logs warnings to slack
- or you could do the simple adding function from statsbomb to trigger both warnings and errors 
- then is triggered by a simple eventbridge client which pushes messages to eventbridge

---

- so binding sources in pareto is probably an antipattern 
- instead this should be done at the expander level 
- event could be defined as table bucket queue or global/inbound 
- expander finds the source arn and includes it in the pattern
- this is done at the dsl runner level 
- or maybe the templater level as has to be a ref rather than a string value 
- so general trend is that pareto dsl is probably doing too much, and more stuff should be moved into expander
- so by the time you split pareto2 DSL into global and local elements, each might be quite small
- expander should also do JSON schema validation
- this extension of expander is a good reason to try and implement API gateway 2
- because you can remove redeployer and have a smaller footprint 

### task queue 17/03/24

- lightbulb moment
- queue should push to eventbridge
- that way a queue is handled in a manner similar to the streaming table
- it means all the sync lambdas are handler in a similar manner, via inline lambdas 
- it therefore means at the worker level, everything is async
- either eventbridge or sns
- means queue can be handled inline and you probably don't have to worry about retry behaviour 
- as queue to lambda to eventbridge is not going to fail
- big change is that you can no longer define a queue at the lambda level
- instead you have to define it at the app level and you may need to define multiple queue 

### worker roadmap 14/03/24

- event config to stop retries
- subscription filter, log group, log stream
- SlackWebookFunction loads inline code
- bucket, table, topic, builder events

### family multi pack mixin 13/03/24

- FamilyMultiPackMixin allows subclasses to be referenced via their subclass names rather than their base class names
- it's normally more useful to reference from base class names, but there are a couople of cases where subclass naming is useful
- generally where -
- a) you have more than one subclass of a particular resource
- b) you need instances of more than one subclass in a particular namespace
- examples -
- 1) apigateway 4XX|5XX gateway responses
- 2) website recipe requiring S3 proxy method and also root redirect method
- note that a simple has-many relationship (eg endpoints to apis in webapi receipe) doesn't strictly meet condition b)
- but since method includes family pack to help website pattern, it's useful for webapi endpoints to follow this pattern also

### component review 12/03/24

- eyeball generated JSON for deficiencies, particularly in arn formation
- check list of resources created, old _components versus new components
- iterate through new JSON; compare construction of each resource with old _components resource

### namespaces, components, parameters, templates 10/03/24

- in addition to the below, namespaces are very powerful
- as cloudformation operates in a single global namespace
- so namespaces-as-prefixes are very useful
- so logical id = #{namespace}-#{resource-name}, which can be implemented via a property
- the nice thing about this is that a component can then include resources from different aws packages in a simple mannee, which is a core required skill
- a component doesn't have a namespace of its own because it may need to operate across multiple namespaces, particularly parent/child as per relationship between api and multiple endpoints
- (have to construct one namespace per endpoint)

---

- for parameters you have a number of options
- 1) hardcode values in template
- 2a) explicitly define parameter
- 2b) auto- fill implied parameters
- I don't think 1) is the solution as parameters are typically environment variables such as domain name or certificate arn
- stuff which must come from outside once a template has been defined
- think about giving the template to someone else - you wouldn't want domain name and certificate hardcoded, would you?
- (there is then a second parameter issue of "globals" such as python version or timeouts, which needs considering)

---

- if you are going to auto fill, which may still be the best solution, then a template has to be separate from a component as parameters can only be inferred once a set of resources have been rendered
- so want to roll back existing template class to a component, and turn it back into a list of resources
- component then renders into template
- template can auto fill parameters
- but needs to think about external environment parameters (no defaults) and internal global parameters (has defaults)

---

- component might be better named as resource list
- outputs could be handled via visibility parameter at the resource level
- do you really need parameter globals? this might just be an artifacts of short/medium/long/default stuff
- might be simplier to hardcode integers at the lambda level
- as they seem part of stack structure not environment variables

### 0-8 philosophy xx/03/24

- distinguish between resources and components
- resources live in module/class structure which reflects their aws type
- can extend base classes with useful default configurations
- eg SimpleEmailUserPool, streaming table, eventbridge event patterns
- but each class must be able to return its AWS resource type dynamically
- to do this there must *always* be a base class which reflects the aws type name, even if its empty

---

- cloudformation makes extensive use of declarative refs, whether directly using Ref or indirectly using Fn::GetAtt
- majority of resources in a component come from same aws package
- hence default referencing convention should be to use name + resource suffix convention
- but there are exceptions, particularly with respect to glue code
- iam roles, lambda permissions, lambda event source mappings
- here you probably need to override default refs with custom parameters

---

- resource renders down to resource name string and dict of values - Type, Properties, Depends
- component is list of resources
- component will probably render to Parameters, Resources, Outputs
- template is list of components
- components are defined in separate directory
- expectation is that components import a lot of resources
- but may also extend their own, particularly with respect to glue code
- eg api component probably defines/extends nonsense cognito roles, other roles, permissions in a custom manner

### roadmap 03/01/24

- let's assume we manage to refactor layman2 to include local builder
- this leaves pareto2 in a clean ish state but in need of surgery in places 
- mainly around the dsl
- first thing is that it needs some kind of extension system to facilitate custom components such as layman's builder 
- second thing is that the support for global entities (bucket, table, website, API) needs to change In favour of a) auto configuration of bucket and table b) configuration of website and api at setenv level
- this means you can rip out the awful text detection and inferenxe stuff at the dsl level 
- it means you should be able to simplify the schema also and restrict it to lambda related patterns 
- the domain name prefix thing should be simplified in favour of simple fully qualified domain names
- probably API domain name and website domain name should be harmonised 
- these in turn mean the expander templater code can be simplified
- so pareto and expander work in close harmony whilst layman is loosely coupled 
- then it's easier to add lambda alarms and refactor API for apigw2 

### layer naming convention strategy 23/12/23

- old strategy used variables defined in setenv.sh such as "set REQUESTS_LAYER_ARN=#{arn:for:requests}" and then layer refs in infra block such as 'layers: ["requests"]'
- this introduced a layer of indirection as you could easily have "set FOOBAR_LAYER_ARN=#{arn:for:requests}" and 'layers: ["foobar"]'
- conveniently this allowed you to avoid the issue of layer names and how they might be hungarorised
- now you are removing the layer of indirection by allowing layer names to be specified directly in the infra block
- it's a bit awkward as layers are currently named (eg) "layman2-requests-0-1-2" which will hungarorise to "Layman2Requests012"
- but it shouldn't matter as the hungarorised version will only exist under the hood

*** what is crucial is that expander's definition of hungarorise() much match pareto's definition of hungarorise(), specifically with respect to splitting on dashes as well as underscores ***

### glibc 08/12/23

- https://repost.aws/questions/QUrXOioL46RcCnFGyELJWKLw/glibc-2-27-on-amazon-linux-
- https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html

### identity pools 29/03/23

- https://gist.github.com/singledigit/2c4d7232fa96d9e98a3de89cf6ebe7a5

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
