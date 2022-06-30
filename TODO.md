### short [liberate-queues]

- remove md.errors 
- define async error function and queue
- add errors field to action which triggers generation of event config

- add back table error mapping

### pending

- uncomment layers check

### medium

- cdk/__init__.py function to initialise component map
- modify component initialisation to allow nested apis
- check online before performing layers check
- add check so type can't appear in component name
- flatten nested config items where possible
- add API type attr and nest API components 
  - new simple/public API 
- metadata schema
- compact dsl ?

### long

- api w/ key access
- s3 eventbridge connector
- eventbridge urls
- iam role lockdown
- step functions
- appsync + graphql
- aws chat

### thoughts

- consider extending resource name of subordinate types, eg -function-role ?
  - not worth it
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

