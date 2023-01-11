#!/bin/bash
# Call this script from the parent directory
# This will produce wheels using docker
set -e
# remove all .pyc files to prevent error:
# - import file mismatch / unique basename
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
docker pull $DOCKER_IMAGE
mkdir -p dist
docker run -e TRAVIS_PYTHON_VERSION --rm -v `pwd`:/io $DOCKER_IMAGE $PRE_CMD /io/.travis/linux_build-wheels.sh
python setup.py sdist
ls -l dist/
