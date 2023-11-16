### intro

- pareto is essentially an IaC DSL - a small mini- language which expands into cloudformation
- because you want the power of IaC/cloudformation, but you don't want all the hassle
- you want the ability to configure and talk to databases, buckets, queues, apis, event buses ...
- ... but you don't want the ugliness and verboseness of cloudformation, plus the need to maintain a load of completely different stuff away from your code
- but the problem needs as a solution as a "good" serverless app tries to shift as much stuff as possible from the lambda codebase into IaC

### lambda- specific resources

- some IaC resources can be thought of as "belonging to a lambda" eg an API endpoint
- for these pareto uses an `infra` YAML block in each lambda where you can configure your endpoint
- similar for queues, topics, events

### global state resources

- but some resources are global eg table/bucket/website; these aren't bound to a single lambda
- here pareto looks for clues in your code
- if it finds OS references to table/bucket/website it will create that resource for you, and insert the real name under the relevant OS key
- in this way your code can assess these resources, and you haven't even had to declare them!

### the future

- in some ways pareto is very successful; it has a code expansion ratio of about 28:1 and will successfully manage projects with hundreds of linked AWS resources
- but in other ways it's still getting started; still needs proper pipeline code for example, and interface is somewhat half-  baked
- the real future may be a language which compiles down to cloudformation
- eg winglang https://www.winglang.io/

