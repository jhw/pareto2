### sync/async lambda checks 30/06/22

- sync lambdas are bound to queues or apigw
- async lambda should have an errors function
- pretty sure timers aren't async
- worth checking that each lambda is either bound to a queue or apigw, or has an errors declaration, or possibly neither

### cross references 22/06/22

- event action against action names
- timer action against action names
- endpoint actions against action names
- endpoint userpool against userpool names
- event router against routers
