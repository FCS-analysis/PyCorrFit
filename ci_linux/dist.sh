#!/bin/bash
# Call this script from the parent directory
# This will produce wheels using docker
set -e
mkdir -p dist
mv wheelhouse/*.whl dist/
python setup.py sdist
ls -l dist/
