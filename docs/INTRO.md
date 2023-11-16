### deployment and IAM

- for the minute, everything is deployed from the command line
- (I have plans to build pareto pipeline code which would replace this, but this is still on the drawing board)
- so to deploy you need a deployment user, with a role policy which includes permissions for the following -

[list]

- then you need to define a command line profile  on your local machine which references this user

### artifacts

- you can't deploy anything without an artifacts bucket, because large lambdas have to be pushed to s3 for deployment
- (again I have plans for a deployment app with a single bucket which would do this)
- for now you have to manually create a deployment bucket for each app, with bucket name the same as `#{app-name}` plus an `-artifacts` suffix
- there are tools in `pareto/scripts/artifacts` to help with this

### app structure

- pareto assumes you have a large number of lambdas in a single Python package, each with its own directory
- must have an index.py file containing handler code
- must have a test.py file containing test code (see below)
- can have as many other files/modules in directory as you like
- each index.py file must contain a yaml block at the top, which contains an `infra` key (sort for `infrastructure`; see below)

### testing

- (not strictly related to the environment, but worth noting as pareto has strict views about it)

- big problem is slowness of cloudformation
- even a small change can take 45 seconds to deploy
- so if you're finding indentation errors in your lambda code in production, your productivity is being ruined!
- hence try and find 95 pct of lambda bugs in development
- use moto to mock core services, particularly s3 and dynamodb
- write fixtures to mock s3/dynamo before test runs; lambda picks up mock data; lambda saves more data back to s3/dynamodb; assert data saved is as you expected
- yes you have the pain of writing test code, but the alternative (permanently broken code) is worse
- critics will say "moto never a full copy of AWS" but that's not what you need; you just need it to be rock solid for the core services
- IMO this works well and reduces errors down to permissions and gaps between lambdas
- former are trivial to fix and latter should be covered by integration tests

### infra

- `infra` blocks are core to pareto
- is basically a small DSL for infrastructure-as-code which expands into cloudformation
- idea is to "define you IaC alongside (within) your code" for simplicity
- will write a separate doc detailing the main bits and pieces you can include within infra

### infra OS variables

- the second "special" (!) part of pareto
- pareto searches code for specific OS variables referenced within your lambda code, as clues for global state resources to create for your app
- general format is `os.environ["#{app-name.upper()}_(TABLE|BUCKET|WEBSITE)"]`
- if pareto finds any of these refs in your code it will automatically create a) a dynamodb table b) a private s3 bucket c) a public s3 bucket for you
- pareto creates these resources under the hood and then injects their names  (created randomly) into the lambda os environment using the key format above (hence `os:environ`), so these state resources are accessible
- state resources such as table/bucket/website are defined in this way (and not in the `infra` yaml block) as they are "global" to your app and do not belong to a particular lambda
- any state resource created will automatically stream insert/update/delete events into eventbridge, so you can trigger lambda functions from state events
- (there is probably a better way to do this, but it probably involves designing a mini- language and writing a compiler - see winglang (https://www.winglang.io/)

### domain names

- pareto assumes you are building a suite of services of microservices under a single domain name
- domain name format is "#{app-prefix}.#{domain-name}
- you have to purchase the domain name via route53 console
- purchase should automatically create a record set for that domain name
- pareto has tools in `/scripts/domains` to configure the domain name for you, in particular adding a certificate
- don't try to create/link certificate manually! All sorts of painful stuff like locating in `us-east-1` etc

### layers

- assume you're going to need packages outside stdlib
- don't want to deploy these with app as some are huge
- pareto assumes you create one layer per package
- deployed layers have ARNs which are then referenced as os variables within apps
- pareto has tools to create layers in `scripts/layers`
- again don't try creating layers manually as is a total pain 
