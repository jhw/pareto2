### Console

https://cloud.google.com/?hl=en
https://console.cloud.google.com/welcome

Create Projects -> Polyreader OAuth Creds

https://console.cloud.google.com/welcome?project=polyreader-oauth-creds

### Enable APIs

https://console.cloud.google.com/apis/dashboard?project=polyreader-oauth-creds
https://console.cloud.google.com/apis/library?project=polyreader-oauth-creds

Enable Cloud Resource Manager API
Enable Identity and Access Management (IAM) API

### OAuth generation

https://console.cloud.google.com/apis/credentials?project=polyreader-oauth-creds

(you should see the APIs and Services menu on the LHS)

##### Configure consent screen

External
Home page -> https://home.polyreader.net
Authorised domain -> polyreader.net

##### Add scopes

openid: This scope is necessary for OpenID Connect (OIDC) authentication.
email: This scope allows access to the user's email address.
profile: This scope provides access to the user's profile information.

However, Google scopes are prefixed with the base URL for Google APIs, so you should use the following when explicitly entering full scopes:

OpenID: openid
Email: https://www.googleapis.com/auth/userinfo.email
Profile: https://www.googleapis.com/auth/userinfo.profile

You can use the filter screen and select, but will need to remove the filters to see everything that has been selected

##### Test users

Add your own email address

### Credentials

Credentials -> Create Credentials -> Create OAuth client id
Web application
Authorised javascript origins -> https://polyreader.net
Authorised redirect URIs -> https://polyreader.auth.eu-west-1.amazoncognito.com/oauth2/idpresponse
Hit create and download creds

### Testing and deployment

```
The message "OAuth access is restricted to the test users listed on your OAuth consent screen" appears because the OAuth consent screen is configured as an "External" application in "Testing" mode. In this mode, only the users you explicitly list as test users can access the OAuth application.
```

On the OAuth consent screen there is a "Publish App" button to make the app public

### gcloud

```
gcloud projects list
```
