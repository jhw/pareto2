### short

- use local table definition
- handle multiple tables
- handle multiple routers

- rename errors as errors/async
- new errors/sync
- bind table to errors/sync
- add errors/sync handling to queues
- simplify validate_async_errors

### medium

- table stream shouldn't be defined as part of config
- cdk/__init__.py function to initialise component map
- modify component initialisation to allow nested apis
- add check so type can't appear in component name
- extend resource names suffixes for subordinate types
- flatten nested config items where possible
- add API type attr and nest API components 
  - new simple/public API 
- metadata schema

### long

- s3 sync error handling
- lambda alarms
- api w/ key access
- s3 eventbridge connector
- eventbridge as lambda destination
- eventbridge urls
- iam role lockdown
- step functions
- appsync + graphql
- aws chat

### thoughts

- failure options for s3 notifications ?
- is s3 invocation of lambda is synchronous ?
- compact dsl ?
- clean up all init resource/output functions ?
  - not worth it
- avoid userpool/userpool_ nomenclature ?
  - not worth it
- stop symlink creating pareto2/pareto2 ?
  - probably overkill at this stage
- action to validate binding uniqueness ?
  - probably overkill at this stage
- remove eventbus discoverer ?

### done

- handle multiple buckets
- replace EventsEventBusName/EventsQueueName/EventsRulePrefix with router name
- check failure options for s3 notification configuration
- check for invalid error handlers
  - if bound to apigw
  - if bound to table
  - if bound to bucket
  - if bound to queue
- remove error handlers from bucket/table configurations
- rename binding as mapping
- validate table errors attr
- add back table error mapping
- check online before performing layers check
- uncomment layers check
- validate errors field against action
- add errors field to action which triggers generation of event config
- define async error function and queue
- remove md.errors 
- remove queue errors dlq
- comment out event config generation
- don't define event_config for sync actions
- refactor queues.py to work off queue config not action config
- refactor queue config in pareto2-demo
- add new metadata queue class
- validate queue action against actions
- make bucket, table action optional
- replace dynamic imports
- investigate why some stack names are pluralised
- investigate why list of stack names is required in metadata
- pluralise all plural component modules
- check StackName refs
- rename bucket and table as demo-streaming
- validate bucket, table action
- add bucket, table action
- avoid duplicating schema stuff with metadata validation code 
- event action / source validation
- api endpoints against endpoint names 
- event router against routers
- api userpool against userpool names
- endpoint actions against action names
- event action against action names
- timer action against action names
- add cross validation to all cross references
- list all cross references 
- use endpoint["name"] rather than endpoint["action"] in api resource names
- get rid of actions.names
- shouldn't need actions.functions any more
- don't think u really need these `rules` properties
- think timer.rules should reference `name` not `action`
  - see if this allows you to have different `name` and `action` attrs in config
  - repeat for events
- liberate events from actions
- liberate timers from actions
- move timers validation into new md.timers class
- bind endpoints to APIs 
- move endpoint validation code from action into endpoint
- $schema declaration is missing
- investigate why new api template post- endpoints integration is slightly smaller than prior template
- api component to use md.endpoints
- remove endpoints from actions
- separate endpoint from actions
- bind endpoints to apis
- apis to specify user pool
- events to specify router
- add support for list of userpools
- rename users as userpool
- md.routers is blank
- rename routing as events
- rename events as router
- convert buckets and tables to be lists
- convert dash to handle bucket and table lists
- copy config
- allow option to ignore lambdas if required
- test deploy_stack.py false
- remove unauthorised api
- remove self.env declarations from test

