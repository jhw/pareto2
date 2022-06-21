### short

- rename events as router
- convert routers to be list
  - will require all action events to specify router

- actions must be specified as part of api
- pluralise all components modules which now take lists

- convert users to be list
- apis to specify user pools

- components/api to be a package with root/open/cognito apis
- consider if there are any other cross- component references
- re- check how table, bucket reference functions
- check how to define and import a pip branch rather than a tag

- stop symlink creating pareto2/pareto2

### medium

- can't run component main scripts as metadata does not exist

### long

- api w/ key access
- s3 eventbridge connector
- eventbridge urls
- iam role lockdown
- step functions
- appsync + graphql
- aws chat

### thoughts

- cross check bucket/table names against mapped streaming functions?

### done

- convert buckets and tables to be lists
- convert dash to handle bucket and table lists
- copy config
- allow option to ignore lambdas if required
- test deploy_stack.py false
- remove unauthorised api
- remove self.env declarations from test

