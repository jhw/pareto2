#!/usr/bin/env bash

. config/app.props

if [ -z $1 ]
then
    echo "Please enter action"
    exit 1
fi

if [ -z $2 ]
then
    echo "Please enter template file"
    exit 1
fi

if [ -z $3 ]
then
    echo "Please enter stage"
    exit 1
fi

aws cloudformation $1-stack --stack-name $AppName-$3 --template-url https://s3.$AWS_REGION.amazonaws.com/$ArtifactsBucket/$2 --parameters ParameterKey=StageName,ParameterValue=$3 --capabilities CAPABILITY_NAMED_IAM
