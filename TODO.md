### short

- allow invocation check to assume async functions by default
- action decorator to insert async

### medium

- separate sync, apigw types
- add back s3, ddb dashboards
- investigate adding app name to dashboard

### paretocli

- refactor search lambda logs

### long

- wheel package
- apigw api keys
- lambda alarms
- apigw logging

### thoughts

- consider refactoring event topic, pattern as head, body?
  - think topic, pattern probably more naturalg

### done

- timer function size, timeout
- apply function defaults to inline functions
- refactor demo.yaml
- dsl to validate event sources
- refactor dash main block
- convert "short" to "default"
- add default size/timeout parameters (small, short)
- add arn support to action env vars
- remove paretodemo
- add env vars to demo.yaml
- check whether action env vars takes list or keys
- check what the api auth-type parameter is doing in __main__
- ensure topic/pattern/source are optional params
- add event topic attr which pattern matches against detail-type 
- remove template validation from component blocks
- check demo has both bucket and table validations
- test event source changes
- replace components __main__ blocks with single version based in template.py
- extend demo
- roll out action __main__ changes to other components
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

