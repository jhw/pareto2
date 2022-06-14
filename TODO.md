### short

- replace PackageRoot with env variable
- consider replacing config with env variables
- add ping scripts and test

### medium

- add error handling and slack
- test hello add with bad errors
  - remember has to be async ping

### long

- replace unathorised api with api tokens
- replace s3 event lambda with direct eventbridge event
- investigate eventbridge direct URL ping for Slack events
- replace slack with aws chat

### thoughts

- cross check bucket/table names against mapped streaming functions?

### done

- test deployment
- complete hello get
- complete apigw handler code and tests
- remove cors endpoints if not authorized
- allow APIGW endpoints to be unauthorized
- PackageRoot is being passed as parameter but not being consumed
- test skeletons
- base test class
- pip package
- github project
- replace package root in defaults
  - use full package name in lambda
- action class should be passed package root
- replace cricket refs
- remove bbc refs
- gitignore
- refactor cdk, scripts roots
- setenv
- pyenv
- requirements
