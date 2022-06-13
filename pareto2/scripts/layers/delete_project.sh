#!/usr/bin/env bash

. config/app.props

aws iam detach-role-policy --policy-arn arn:aws:iam::$AccountId:policy/$AppName-codebuild-layers-role-policy --role-name $AppName-codebuild-layers-role
aws iam delete-policy --policy-arn arn:aws:iam::$AccountId:policy/$AppName-codebuild-layers-role-policy
aws iam delete-role --role-name $AppName-codebuild-layers-role
aws codebuild delete-project --name $AppName-layers
