### short [domains]

- delete_certificate to remove cname record
- add print statements to create_certificate
- poll for issued status

- add _and_cname_record_set suffix to create|delete_certificate.py

### medium

- apigw static endpoint
- sqs error retries
- bad resourcename/depends combo doesn't appear to be being caught
- make database and bucket fixed assets, like errors?
- apigw logging
- userpool should be named private-api
- ability to validate publishing of sns message

### long

- wheel package
- lambda alarms

### thoughts

- seems inconsistent that table has an appname prefix but api does not
- push_artifacts.py didn't seem to throw exception on bad POST schema in infa
  - problem is that endpoint schema is only required to be an object with no validation
- why do I get occasional permissions problems because schema seems to allow (incorrect) attributes at root level ?
  - unclear :(
- check for duplicate event names ?
  - probably not much necessary
- check for empty model schema ?
  - not worth it
- GET endpoint should allow blank parameters ?
  - better to be explicit
- add handler for blank infra (or exception) ?
  - not sure
- validate schema format ?
  - leave as free- form
- infer GET/POST from parameters/schema?
  - no is probably clearer not to
- apply table defaults at root table level?
  - no because is more complex, applied at nested level
- consider refactoring event topic, pattern as head, body?
  - think topic, pattern probably more naturalg

### done

- delete stray CNAME
- try creating CNAME with name provided from
- create_certificate.py to create cname record
- check certificate status 
- create_certificate.py to print record set details
- list_certificate to show status
- add scripts from polyreader2-server
- simplify errors function/role code
- check custom resource depends
- new custom resource
- new logstream function and role
- add slack- prefix to existing errors function
- logs event needs unpacking
- log subscriptions to depend on error permission
- push_artifacts to insert slack_error_webhook
- test by pinging polyreader /show-assets with invalid chunk index
- check that errors function, role, permission exist and are correct
- scripts to add dsl config errors entry
- generate template
- check that each action has a logs subscription
- errors to be loaded by config initialisation
- slack error webhook env variable
- check fn::sub will insert default second arg {}
- error filter pattern
- log subscriptions
- log permission
- per-  action susbscription and permissions 
- function size and timeout (small, short)
- slack handling inline code
- inline function and role singletons borrowed from table
- new errors component
- :64 length check for event rule names
- include ext/test/sqs
- create tagged version

- compare output with amplify flutter issue
  - https://github.com/aws-amplify/amplify-flutter/issues/431

- compare output with gist
  - https://gist.github.com/singledigit/2c4d7232fa96d9e98a3de89cf6ebe7a5

- identity pool role mapping
- identity pool
- add role names
- merge unauthorized/authorized role code
- borrow role creation code from action
- include identity pool output value
- don't think users stuff is being created
- dump output to tmp
- create skeleton identity stuff
- separate test class into per- service modules
- test for inheriting from multiple test classes
- remove callbacks support
- remove dash random components
- which in turn means you need to expand demo 
- then really need check that only one of events endpoint topic queue timer can be set for a specific infra
- see invocation type to sync if queue is present as well as endpoint
- remove action async/queue/apigw types
- scripts to insert sqs permissions if queue detected
- script code to bind queue, timer
- add queue, timer to schema options
- add queue, timer to demos
- add queue, timer components
- add queue, timer to list of imports
- look in event sources for bucket, table definitions
- stop empty bucket, table dashboards from being deployed
- events rule target ids can be local
- all script errors to raise exceptions
- add exception if no infra found
- global defaults support
- endpoint should use path as name
- dehungarorise is messing up bucket/table/topic names
- add checks for mis-specified infra yaml
- Config.initialise

```
Traceback (most recent call last):
  File "/Users/jhw/work/expander/expander/pipeline/templater/index.py", line 156, in spawn_template
    template.parameters.update_defaults(self.config.parameters)
  File "/Users/jhw/work/expander/env/lib/python3.8/site-packages/pareto2/config/__init__.py", line 53, in parameters
    params.update(self[attr].parameters)
  File "/Users/jhw/work/expander/env/lib/python3.8/site-packages/pareto2/config/parameters.py", line 8, in parameters
    return {hungarorise(k):v
  File "/Users/jhw/work/expander/env/lib/python3.8/site-packages/pareto2/config/parameters.py", line 8, in <dictcomp>
    return {hungarorise(k):v
NameError: name 'hungarorise' is not defined
```

- convert demo to use hello/world
- load_files to be able to switch directory
- add ext to demo
- pass ext files to expand()
- expand to initialise scripts
- democratise expand so it takes a list of (path, text) pairs
- render callbacks to config
- aggregate callbacks
- add callbacks to schema with type and body
- type is an enum with oncreate value only
- body is an object
- render secret components > convert value to values
- attach indexes to table
- validate GET+params or POST+schema
- index requires table attribute
- add secret to infra
- add index to infra
- validate permission format
- abstract endpoint attachment
- separate action name and action path
- clean up component main blocks
- create table with empty indexes
- populate action env variables
- remove layers and environments
- action invocation types
- initialise actions after apis
- attach endpoints to apis 
- action size and timeout 
- add userpool ref to private api 
- init userpools if private api
- helpers to create apis
- add APIs if public, private 
- dump apis
- scripts method to filter APIs 
- nested event source type
- add demo events, endpoint, layers, permissions
- add method and API to endpoint schema as required fields, method as enum
- add endpoint parameters and schema fields
- add source, topic, pattern fields to event schema 
- remove extra fields option from schema root 
- define action before appending
- if events, layers, permissions exist in infra, add them to actions 
- add topics as per buckets and tables 
- infra schema validation
- parameter defaults
- streaming table
- scripts class
- aggregate buckets, tables across scripts
- add buckets, tables config
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

