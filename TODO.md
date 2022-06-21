### short

- allow lists of all root components, as per actions
- event requires event bus to be specified
- cross check bus name against available buses
- remove unauthorised api
- api requires user pool to be specified
- cross check pool name against available pools
- components/api to be a package with root/open/cognito apis
- consider if there are any other cross- component references
- re- check how table, bucket reference functions
- check how to define and import a pip branch rather than a tag

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

- remove self.env declarations from test

