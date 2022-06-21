### short

- rename users as userpool
- add support for list of userpools
- apis to specify actions
  - cross check api actions against apis
- apis to specify user pool
  - cross check api user pool against user pools
- events to specify router
  - cross check event router against routers

- pareto2/cdk/__init__.py shouldn't hardcode stack names 
  - and also shouldn't the recently updated ones be pluralised?

- pluralise all components modules which now take lists
- components/api to be a package with root/open/cognito apis

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

