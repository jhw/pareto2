#!/usr/bin/env bash

export AWS_PROFILE=woldeploy
export AWS_REGION=eu-west-1
export PYTHONPATH=.

if [ ! -L config.yaml ]; then
    echo "creating paretodemo symlink"
    ln -s ../paretodemo/config.yaml config.yaml
    ln -s ../paretodemo/paretodemo paretodemo
    ln -s ../paretodemo/fixtures fixtures
    ln -s ../paretodemo/scripts scripts
fi



