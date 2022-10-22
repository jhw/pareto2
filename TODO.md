### short

- test event source changes
- add event topic attr which pattern matches against detail-type 
- ensure topic/pattern/source are optional params
- check whether action env vars takes list or keys
- add default size/timeout parameters (small, short)

### medium

- add arn support to action env vars
- refactor search lambda logs
- add back s3, ddb dashboards
- delete paretodemo

### long

- apigw api keys
- lambda alarms, timeouts
- burningmonk apigw stuff
- appsync + graphql
- lambda powertools

### thoughts

### done

- add explicit event source attr
- rename event source attrs as type (table, bucket) and name
- component main blocks should call template.parameters.validate, template.validate_root
- rename template.validate_root
- create migration script
- remove event action source 
- check/remove parameter mandatory key validation stuff
- replace with completeness check, but with optional ignore arg

- repeat for topics, buckets
- check layer keys against layer values
- stop lambda retries
- rename packages as layers
- renamed defaults as parameters
- merge layers into parameters
- remove any other boto- client related code
- refactor component main block template dumping stuff
- remove template s3 dump code
- action permissions is fucked up if you send wildcard permissions
- fix Config.initialise() refs

