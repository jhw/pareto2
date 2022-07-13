#!/usr/bin/env bash

export AWS_PROFILE=woldeploy
export AWS_REGION=eu-west-1
export PYTHONPATH=.

export APP_ROOT=demo # always override

if [ ! -L demo ]; then
    ln -s ../pareto2-demo/demo demo
    ln -s ../pareto2-demo/config config
    ln -s ../pareto2-demo/fixtures fixtures
fi


