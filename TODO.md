### short

- scripts class
- aggregate buckets, tables across scripts
- add buckets, tables config

- infra schema validation
- apis given endpoint parents
- action environment variables 
- action events
- action callbacks
- action endpoints
- action invocation types
- layer arn population
- table indexes

### paretocli

- simplify push_artifacts
  - remove action env variables
  - remove permisison inference
  - remove schema validation?

### expander

- remove preprocessor schema validation
- remove templater action env variables
- remove templater permisison inference

### medium

- topics could be inferred from env variables 
- suspect secrets can be inferred from env variables also 
- could iterate over ext directory to add custom components
- client migration script

### long

- wheel package
- apigw api keys
- lambda alarms
- apigw logging

### thoughts

- apply table defaults at root table level?
  - no because is more complex, applied at nested level
- consider refactoring event topic, pattern as head, body?
  - think topic, pattern probably more naturalg

### done

- filter environment variables
- add bucketname, tablename os.environ
- script.partition
- add action definition for each index file
- expand to walk through files based on root argument
- new script class to parse infra from code
- pass root to script
- replace file loading with simple inline config
- add basic demo handler in package
- rename DSL as config
- separate config module into per class modules 
- where is the action env variable inference code ?
- remove existing expansions 
- review and document existing expansions - layers, permissions, bindings/type inferences, one more 
- remove all validation code 
- branch 0-4
- populate layer versions should use self.env and shouldnt need env passing to it
- layer population should be part of expansion routine
  - layer population should take entire env struct
- remove cross_validate_layers
- Config.load_file should really just be Config.load
- git push origin :callbacks
- remove randomisation in components, except maybe for dashboard
- remove local components support
- remove timer 
- migration script to add callbacks
- callbacks validation skeleton
- validate callbacks action
- add callbacks class to config (type, action, body)
- liberate bindings class in dsl 
- dev/migrate-0-3-17.py
- init_file to call new expand() method prior to return
- expand to create map of endpoint, topic, timer bindings
- populate invocation type depending on bindings map
- remove dsl invocation checks
- undo env arn support
- add S3, ddb dashboards
- dash to add dashboard name (type, random slug)
- migration script to lookup endpoints and change queue invocation types to apigw
- add DSL support for apigw invocation type
- add action component support for apigw invocation type
- rename sync refs in action component as queue
- refactor sync refs in dsl validation as queue
- migration script to refactor sync type as queue type
- migrator to remove async
- allow invocation check to assume async functions by default
- action decorator to insert async
- migrator to blank table streaming
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

