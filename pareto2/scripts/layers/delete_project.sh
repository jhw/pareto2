#!/usr/bin/env bash

aws iam detach-role-policy --policy-arn arn:aws:iam::$AWS_ACCOUNT_ID:policy/$APP_NAME-codebuild-layers-role-policy --role-name $APP_NAME-codebuild-layers-role
aws iam delete-policy --policy-arn arn:aws:iam::$AWS_ACCOUNT_ID:policy/$APP_NAME-codebuild-layers-role-policy
aws iam delete-role --role-name $APP_NAME-codebuild-layers-role
aws codebuild delete-project --name $APP_NAME-layers
