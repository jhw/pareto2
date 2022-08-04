#!/usr/bin/env bash

. config/app.props

if [ -z $1 ]
then
    echo "Please enter action"
    exit 1
fi

if [ -z $2 ]
then
    echo "Please enter stage"
    exit 1
fi

aws cloudformation $1-stack --stack-name $AppName-$2 --template-url https://s3.$AWS_REGION.amazonaws.com/$ArtifactsBucket/template-latest.json --parameters ParameterKey=StageName,ParameterValue=$2 --capabilities CAPABILITY_NAMED_IAM
