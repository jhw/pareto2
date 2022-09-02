#!/usr/bin/env bash

export AWS_PROFILE=woldeploy
export AWS_REGION=eu-west-1
export PYTHONPATH=.

export PARETO2_APP_PATH=.
export PARETO2_APP_NAME=demo

if [ ! -L demo ]; then
    ln -s ../pareto2-demo/config.yaml config.yaml
    ln -s ../pareto2-demo/demo demo
    ln -s ../pareto2-demo/fixtures fixtures
    ln -s ../pareto2-demo/scripts scripts
fi


