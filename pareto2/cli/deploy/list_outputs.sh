#!/usr/bin/env bash

. config/app.props

if [ $# -eq 0 ]
then
    echo "Please enter stage"
    exit
fi

aws cloudformation describe-stacks --stack-name $AppName-$1 --query 'Stacks[0].Outputs' --output table
