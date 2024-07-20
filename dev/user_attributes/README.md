### strategy

- replace user_attributes inline code with events_push
- replace user_attributes inline code test with event_push test
- change cognito event_push to bind to all relevant hooks
- replace web_api creation of user_attributes function with events_push
- remove userpool attributes from root.yaml api definition
- add userpool event block to templater
- add userpool event to worker.yaml schema definition
- move user_attributes handler into polyreader3
