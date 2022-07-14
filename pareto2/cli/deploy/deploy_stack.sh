#!/usr/bin/env bash

. config/app.props

if [ $# -eq 0 ]
then
    echo "Please enter stage"
    exit
fi

if [ $# -eq 1 ]
then
    echo "Please enter template"
    exit
fi

aws cloudformation create-stack --stack-name $AppName-$1 --template-url http://s3.eu-west-1.amazonaws.com/$ArtifactsBucket/$2 --capabilities CAPABILITY_NAMED_IAM
