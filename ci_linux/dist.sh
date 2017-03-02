#!/bin/bash
# Call this script from the parent directory
# This will produce wheels using docker
set -e -x
docker pull $DOCKER_IMAGE
mkdir -p dist
docker run --rm -v `pwd`:/io $DOCKER_IMAGE $PRE_CMD /io/ci_linux/build-wheels.sh
python setup.py sdist
ls -l dist/
