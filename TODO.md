### short

- apis to specify actions
- apis to specify user pool

- cross check api actions against apis
- cross check api user pool against user pools
- cross check event router against routers

- liberate events from actions as distinct metadata type
- liberate timers from actions as distinct metadata type
- liberate endpoints from actions as distinct metadata type

- pareto2/cdk/__init__.py shouldn't hardcode stack names 
  - and also shouldn't the recently updated ones be pluralised?
- simplify init_resource, init_output routines
- avoid userpool/userpool_ nomenclature
- pluralise all components modules which now take lists
- components/api to be a package with root/open/cognito apis
- metadata schema validation

### medium

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

- remove eventbus discoverer ?
- cross check bucket/table names against mapped streaming functions?

### done

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

