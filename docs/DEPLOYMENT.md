### overview

- deployment of pareto apps is currently done exclusively via the command line
- a three stage process - test, build, deploy.

### running tests

- python scripts/build/run_tests.py
- pareto is very opinionated about testing
- expects you to have a test.py file for every index.py handler file
- run_tests.py extracts all test classes from test.py files and runs them as a single test suite
- standard handler will read from s3/dynamodb, run some stuff, save back to s3/dynamodb
- best practice is to have test classes mock these aws services
- the reason you want to do this is because cloudformation is slow; at least 30 secs for even small deployments
- so you don't want to be finding indentation errors in production!
- mocking with moto can help catch the majority of errors at development stage
- remaining errors tend to be permission errors or gaps between services
- former are easily solved; capture the latter with integration tests
- you don't have to run tests but highly advisable to do so
- critics will say moto not a full copy of aws (true) but you only need it to cover the core primitives solidly (which it does)
- pareto has mixin classes for core resources (s3, dynamodb) which help you manage the mock resource lifecycle

### push artifacts

- push artifacts analyses code and builds cloudformation template
- as discussed elsewhere, looks in three places
- infra blocks in lambda files for lambda- specific resources (api endpoints, event definitions, queues, topics)
- references to stateful resources in OS variables (table, bucket, website)
- environment variables defined in setenv.sh (layers, API keys, slack webhooks)
- the resulting template is pushed to s3 for deployment
- templates are time stamped but template-latest.json is also saved
- you can inspect it by fetching it from s3 with scripts/artifacts/fetch_object.py

### deployment

- python scripts/deploy/deploy_stack.py
- deploys template-latest.json from s3
- template includes reference to latest timestamped lambda artifacts, also sitting in s3

### the future

- in the future all the above scripts would be replaced with dedicated applications
- expander takes zipped pareto app, runs tests, runs artifacts building, pushes lambdas and cloudformation template to deployer S3 bucket.
- deployer expands zipped lambdas and cloudformation file, deploys app
- watcher watches Github repo for new tags and branches, pulls new code and pushes to expander
- no longer any need for app- specific artifacts bucket
- need for scripts/debug withers away as each app has its own UI with which you can view deployment events
- for every boto3 script you have, there is usually an app which is better suited to take its place!


