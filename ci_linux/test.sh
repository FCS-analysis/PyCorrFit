#!/bin/bash
# Call this script from the parent directory
# This will produce wheels using docker
set -e -x
source ~/env/bin/activate
pip install coverage coveralls
coverage run --source=pycorrfit ./setup.py test
coverage report -m
coveralls

