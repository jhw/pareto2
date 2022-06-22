### short

- list all cross references 
- add cross validation to all cross references

### medium

- clean up all init resource/output functions 
- pluralise all plural component modules
- investigate why list of stack names is required in metadata, and why some are singular / some plural
- add API type attr and nest API components 
- new simple API 
- avoid duplicating schema stuff with metadata validation code 
- avoid userpool/userpool_ nomenclature
- metadata schema
- stop symlink creating pareto2/pareto2

### long

- api w/ key access
- s3 eventbridge connector
- eventbridge urls
- iam role lockdown
- step functions
- appsync + graphql
- aws chat

### thoughts

- move events validation into new md.events class ?
  - removed as very dependant on nesting within functions
- remove eventbus discoverer ?
- cross check bucket/table names against mapped streaming functions?

### done

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

