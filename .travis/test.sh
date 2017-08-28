#!/bin/bash
set -e
pip install coverage codecov
coverage run --source=pycorrfit ./setup.py test
coverage report -m
# allow codecov to fail
codecov || exit 0

