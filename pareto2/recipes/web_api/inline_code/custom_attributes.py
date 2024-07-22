"""
- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-cognito-userpool-schemaattribute.html
- unfortunately custom attributes have to be defined at pool creation time, not runtime
- a custom attribute value in your user's ID token is always a string, for example "custom:isMember" : "true" or "custom:YearsAsMember" : "12".
- you do *not* use `custom:` prefix when defining in cloudformation, but you *do* need same prefix when referencing from boto3
"""

import boto3, json, os

from botocore.exceptions import ClientError

"""
- admin_get_user throws ClientError [UserNotFoundException]
- this needs to be handled as when triggered by some of the different Cognito hooks, a user may not exist yet
"""

def fetch_attribute_values(cognito, user_pool_id, username):
    try:
        user = cognito.admin_get_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        if "UserAttributes" not in user:
            print(f"User {username} has no attributes")
            return None
        return {attr["Name"].split(":")[1]: attr["Value"]
                for attr in user["UserAttributes"]
                if attr["Name"].startswith("custom")}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UserNotFoundException':
            print(f"User {username} not found: {e}")
        else:
            print(f"An error occurred: {e}")
        return None

def update_attribute_values(cognito, user_pool_id, username, attributes):
    cognito.admin_update_user_attributes(
        UserPoolId=user_pool_id,
        Username=username,
        UserAttributes=attributes
    )

"""
- event pushed to Eventbridge so custom handlers can trigger off it
"""

def push_event(events, event):
    entry = {"Detail": json.dumps(event),
             "DetailType": "event",
             "Source": event["userPoolId"]}
    batch = [entry]
    events.put_events(Entries = batch)
    
"""
- Cognito handler always needs to return the event! (sync call)
- only update values if they don't already exist; don't want to wipe over changed values with defaults (remembering that some Cognito looks trigger on every login)
"""
    
def handler(event, context):
    cognito, events = (boto3.client("cognito-idp"),
                       boto3.client("events"))
    user_pool_id, username = (event["userPoolId"],
                              event["userName"])
    attributes = json.loads(os.environ["USER_CUSTOM_ATTRIBUTES"])
    existing_values = fetch_attribute_values(cognito, user_pool_id, username)
    if existing_values == None:
        return event
    new_values = [{'Name': "custom:%s" % attr["name"],
                   'Value': str(attr["value"])}
                  for attr in attributes
                  if attr["name"] not in existing_values]
    if new_values ==[]:
        return event
    update_attribute_values(cognito, user_pool_id, username, new_values)
    push_event(events, event)
    return event


