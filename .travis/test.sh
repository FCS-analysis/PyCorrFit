#!/bin/bash
set -e
pip install coverage coveralls
coverage run --source=pycorrfit ./setup.py test
coverage report -m
coveralls

