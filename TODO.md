### short

- teardown, redeploy, test

### medium

- add back (macro, micro) timer w/ tests

- ** dynamic loading of modules from inside layer **

- schema validation
- convert async action error to push to sns 
- table streaming error handlers
- add back events dashboard
- add inline functions to chart generation

### long

- apigw api keys
- lambda alarms, timeouts
- burningmonk apigw stuff
- appsync + graphql
- lambda powertools

### thoughts

- deploy_stack.py to check s3 artifacts ?
  - almost certainly overkill; aim is not to provide a high level of command line comfort
- test underscores in component names?
  - don't think is required
- md.expand() to infer iam roles?
  - problem is it's hard if boto calls are contained in subroutines defined outside index.py
- rename app root as Pareto app root ?
  - think is fine as just APP_ROOT for now
- shouldn't need event type ?
  - I think you probably do
    - relying on just 'bucket' or 'table' isn't explicit enough
- do you need ddb key as part of table event ? 
  - is probably fine
- eventbridge lambda destinations ?
  - probably not relevent if you're going to pipe errors to sns
- eventbridge destination urls ?
  - probably not relevent if you're going to pipe errors to sns
- table inline code to calculate diffs ?
  - no; think you don't need it; it's enough to provide old and new images
- abstract iam role, inline function code ?
  - no because every component has to be named using hardcoded suffixes and may require custom extension
- combine cli push and deploy ?
  - it's a minor pain but I think they should be separate
- queue+function?
  - don't think this is going to work because, unlike table, a queue must always be bound to a user- specified function
- per- stage config ?
  - don't feel like this will work
  - still to be handled on per- branch basis?
- consider removing table error handling ?
  - no seems valuable tbh
- add check for function name conflict  ?
  - it's implicit because -function suffix != -timer-function suffix
- timer checks for exceeding queue length ?
- python deployment script ?
  - is probably fine to have just a shell option, even if slightly more inconvenient; you're not supposed to be investing in the cli really
- codebuild output option
 - https://stackoverflow.com/a/67192915/124179
- some kind of s3 error on stack deployment ?
  - replaced py version with sh
- change deployent to use template body rather than template URL ?
  - problem is max of 51.2k bytes
- codebuild project ?
  - not sure it's a core component, more like a something one- off
- check metadata components can be optional ?
  - not really possible with current metadata structure which uses objects
  - not even sure is really desirable; may be better to explicitly all keys but then allow them to be empty lists
- flatten nested config items where possible ?
  - no real need if no metadata schema, and possibly not even then
- dashboard should not require specification ?
  - think it's probably best made explicit for now
- add check so type can't appear in component name ?
  - probably too tightly prescriptive
- replace action with function ?
  - no particular need, esp if no type checking as per above
- consider nesting events under router ?
  - no think things are fine as they are 
- table stream shouldn't be defined as part of config ?
  - no is fine; is already abstracted somewhat
- simplify validate_async_errors
  - no is fine
- use QueueNamePrefix when looking up queues ?
  - probably not worth it
- failure options for s3 notifications ?
- is s3 invocation of lambda is synchronous ?
- compact dsl ?
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

- error role
- inline error function
- event config
- remove env var printing
- allow additional components paths to be specified in os.environ
- interative functions to validate action/table/bucket refs 
- all arguments in push artifacts to be triggered off os.environ app root
- add schema to post data schema
- add back setting of action environment values
- add metadata.expand method
- investigate why singularising component names "just worked"
- convert metadata to simple dict
- singularise component names
- bad ref to user pool in scripts users admin create 
- remove sqs testing code 
- redeploy and test
- clean up pareto demo scripts
- get rid of metadata expansion
- remove timers and queue actions (replaced with sync/async)
- get rid of metadata classes
- consider removing custom routers
- codebuild, webhook [action?] event rule support
- how does layman2 codebuild pattern work?
- drop table event ddb root prefix 
- add sqs permissions to all actions
- test timer bound to demo-target?
  - replace demo-target2 with sqs permissions for demo-target?
  - new action type which adds sqs permissions but no queue?
- timer apparently no longer working :(
- eyeball template
  - timer event/child looks well specified
  
- sqs permissions enabled
- event rules look well specified
- table streaming included
- detail is getting double nested
- event rules are not getting defined / details are getting messed up
- no way to see template if validation error occurs

```
Error: Invalid mandatory parameters - StageName, DemoTargetDemoBucketEventRule, DemoTargetDemoTableEventRule
```

- remove queue as component type
- additional permissions for queue action
- queue and binding for queue actions
- initialisers for each action type
- add s3 source
- refactor event naming
- iterate through events and add rules
- define router if dynamodb
- make paths explicit in push_artifacts.py
- does timer need delete message

```
DemoTimerQueueBinding => Resource handler returned message: "Invalid request provided: The provided execution role does not have permissions to call DeleteMessage on SQS (Service: Lambda, Status Code: 400, Request ID: 79a59acd-3030-46a0-925c-c2bfc6668c26)" (RequestToken: 017e94c9-497c-bac4-b22b-89928233c7f5, HandlerErrorCode: InvalidRequest)
```

```
DemoHelloMultiplyQueueBinding => Resource handler returned message: "Invalid request provided: The provided execution role does not have permissions to call ReceiveMessage on SQS (Service: Lambda, Status Code: 400, Request ID: 673e516b-3adf-4375-9bf2-1710f3ca3a5e)" (RequestToken: 942dfae3-5ed9-5465-9230-1f07fae4aadb, HandlerErrorCode: InvalidRequest)
```

- ensure unit tests results are captureable
- see if timer really needs sqs:ReceiveMessage
- try and remove sqs wildcards at metadata level
- test re- addition of sqs:* to hello multiply
- specify granular table, timer permissions
- specific logs permissions

```
DemoHelloPostFunctionRole => Actions/Conditions must be prefaced by a vendor, e.g., iam, sdb, ec2, etc. (Service: AmazonIdentityManagement; Status Code: 400; Error Code: MalformedPolicyDocument; Request ID: 7e1114b9-c805-493c-be65-f8ff59158bbc; Proxy: null)
```

- check and replace other non- action, non- table errors with dedicated inline functions
- pass memory, timeout to ddb table code
- nest table router, debug under streaming
- remove event, sqs code in tests
- remove event as first class component
- remove builder as first class component
- remove events as default action permission
- refactor push artifacts so doesn't assume stuff is in root
- remove deploy_stack.py code checking tmp/
- add bucket as event source
- re- test bucket
- add back s3 event
- test bucket example
- re- test table example
- add source to table event
- ensure permissions uses a set to avoid being defined twice
- add top- level debug option to function
- re- integrate table function code
- add debug option to table
- undo NewImage check 
- allow specification of table function as event source 
- create new tag
- destroy and redeploy pareto2-demo
- ping table test
- confirm works and diffKeys present in tail events
- integrate new diffkeys code
- calc diffs and include
- eventName should be part of top level ddb struct
- new Key class with __str__
- find dynamodb event example
- abstract inline code into dev and test with event
- include eventName in table key
- check you can search for inline functions logs
- fix topic policy specifying events as principal
- remove pattern permissions
- add memory, timeout to inline functions

```
DemoTableMapping => Resource handler returned message: "Invalid request provided: The provided execution role does not have permissions to call SendMessage on SQS (Service: Lambda, Status Code: 400, Request ID: 8fc12441-fb29-4e70-8c6b-1d83b6025157)" (RequestToken: 89363dfa-472f-60f0-4f77-5e4a865cf5a3, HandlerErrorCode: InvalidRequest)
```

- check dev branch compiles
- check demo has a table pinging script
- deploy and test master ping
- add back new image check 
- unpack streamconfig
- move stream config inline 
  - replace with streaming boolean
- add md.routers 
- add table router validation
- ensure binding references inline function
- refactor role default permissions
- add (optional) table router 
- ensure function passes environment variables
- remove table action validation
- replace router name in inline code
- replace eventbridge batch size in inline code
- add inline code
- ensure streaming is an option at the dsl level
- add function, role

```
KeyError: 'QUEUE_URL'T
```

- modify handling of event type
- inspect event type


DemoTimerTimerFunction => Resource handler returned message: "Runtime and Handler are mandatory parameters for functions created with deployment packages. (Service: Lambda, Status Code: 400, Request ID: 2eb472e5-1619-4c83-ab34-22fb58025205)" (RequestToken: 30d281e0-31a0-8bd6-e43c-c41d87fe75b9, HandlerErrorCode: InvalidRequest)
```

- bad permission wildcard specification

"""
Error: An error occurred (ValidationError) when calling the CreateStack operation: Template error: resource DemoTopic does not support attribute type Arn in Fn::GetAtt
"""

-  DemoTopicPermission -> SourceArn doesn't need to specify GetAtt, can just specify the topic directly

- template-latest.json not getting created
- move demo timer defaults into metadata
- added timer input variable
- add temporary root config which dumps body
- refactor pareto2-demo timer example
- permission to apply to (root) rule rather than (child) queue ?
- check ref wiring
- permission arn and source
- remove interval from timer
- is interval specified in milliseconds ?
- pass queue name and interval as lambda args
- harmonise runtime handling with action
- notes regarding lack of args being passwed to function
- runtime still being passed as an argument
- revert back to single timers module
- include lambda code
- simplify permissions
- lambda default args
- move timer into timer/__init__.py
- rename root timer
- add function and permission
- add inline code
- add queue
- add queue binding
- abstract validate_actions
- sns template currently displays both demo- and layman2- names
- complete topic policy
- classes to validate action
- parallelise dashboard classes
- parallelise template names
- new component
- new classes
- rename event source/action as action/target
- replace dump_local for core/components main scripts
- event `bucket` attribute to pattern- match s3 eventbridge notifications
- script to download artifacts
- cli/artifacts dir which is pre- populated with bucket
- test push_artifacts.py
- test list_contents.py
- convert s3 push to use in- memory zip
- remove local dumping
- in- memory zip test
- move artifacts into cli/deploy
- upgrade user scripts
- router should be an option for event
- s3 eventbridge notifications
- add codebuild s3 logs
- remove builder completed
- include builder
- re- raise exception if tests fail and is_codebuild
- abstract latest template url
- new python deploy stack script which checks
- deploy stack to use latest template 
- copy template to latest.json 
- copy template to latest.json 
- add template as default template mame
- remove template naming option
- populate pyyaml arn
- deploy and check layer works
- codebuild notifications
- check will pass thru layerppyaml values in defaults
- check layer refs in pareto2-demo
- remove core/components/layer
- remove cli/layers
- upgrade moto to get mock_codebuild
  - requires changes to sqs
  - remove docker
- replace metadata data- binding solution
- remove queue redrive
- consider removing table errors
- remove sync/async errors
- try moving layer params into app.props
- pass template name
- check try/catch positioning in artifacts building
- pass logger to artifacts building
- add notes re codebuild halting
- artifacts.py to take cli args for options
- codebuild mode to generate stack without timestamp, or symlink
  - check for codebuild os variables and just save to main.json
  - don't push to s3
- component path option for template
- separate build_lambdas, build_template
- move template parameter validation code in actions/artifacts.py into template
- change template.dump_local so takes local_filename by default
- fix bad ref to dump_yaml in core/components/__init__.py
- run tests option
- move template dump code
- move artifacts dump code
- helper to list default, optional components
- check only optional component is StageName
- add notes re metadata suitability for extension
- add multiple paths to init_template
- remove stagename from all component main blocks
- rename MyTable etc as TestTable
- build_artifacts shouldn't accept stagename
- simplify (template) autofill_parameters with Parameter class
- remove _json suffix from filename, dumping
- Template shouldn't extend dict but should then have a render method
- separate template Parameter/Resource/Output classes
- refactor cli api
  - combine lambda test/push, template generation/validation into single step
  - embed all variables in template
  - simple deployment stack
- check deploy_stack creates template with correct URL (timestamp)
- deploy stack
- build_artifacts to push lambdas to s3
- build_artifacts to push template to s3
- populate template defaults
- assert every template param has a default value
- avoid hardcoding paths in build_artifacts
- move deployment script into cli
- how to capture unittest errors
- build_artifacts to test lambdas
- simplify layer code in deploy_stack.py by reference to md.layers
- move lambdas inline
- remove template generation, template validation, lambda test, lambda push from deployent script 
- change deploy stack to ask for filename and create template
- create artifacts to dump output file name
- check a Template can be initialised from a JSON struct
- move parameters inline into deployment
- remove stuff below flag in create artifacts
- remove flag from deploy stack
- split deploy stack into two scripts, create artifacts and deploy stack
- move deployment related code into pareto deploy 
- flatten both pareto deploy and pareto cli
- consider renaming pareto deploy as pareto actions 
- run_tests.py no longer finding any lambdas
- move test into pareto core
- remove errors restriction on actions bound to queues
- rename packages as pareto.core, pareto.cli
- scripts/deploy/redeploy_api.py will fail
  - check all scripts which rely on outputs
- raise error if events pattern is not a dict
- add pattern matching utility
- remove eventbridge message analyzer
- add back setenv.sh
- check where setenv has gone
- stuff doesn't get produced if `-dashboard` suffix not specified
- remove types from names
- errors queue can't have its own dlq
- validate apigw type
- validate userpool if cognito
- new simple, cognito apigw
- add type to apigw
- add router suffix
- add event, timer resource suffixes
- extend resource names suffixes for subordinate types
- refactor sqs handlers with decorator which tests for http prefix
- cdk/__init__.py function to initialise component map
- queue did not fail when bad action listed
- add errors/sync handling to queues
- rename errors as errors/async
- new errors/sync
- bind table to errors/sync
- simplify/harmonise timer/root, errors tests
- fetch_queue helper
- timer root should set queue in env using name
- add (router) prefix to events lookup
- drain_sqs to drain by name ?
- rename events-queue as events-target queue
- remove self.queues state
- teardown_events to lookup and delete sqs queue
- delete queue based on name
- queue listing utilities
- bucket test code to work with objects
- fix lambda test error
- check deletion of rules and targets
- re- test router code
- pass router object
- handle multiple routers
- use local table definition
- handle multiple tables
- handle multiple buckets
- replace EventsEventBusName/EventsQueueName/EventsRulePrefix with router name
- check failure options for s3 notification configuration
- check for invalid error handlers
  - if bound to apigw
  - if bound to table
  - if bound to bucket
  - if bound to queue
- remove error handlers from bucket/table configurations
- rename binding as mapping
- validate table errors attr
- add back table error mapping
- check online before performing layers check
- uncomment layers check
- validate errors field against action
- add errors field to action which triggers generation of event config
- define async error function and queue
- remove md.errors 
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

