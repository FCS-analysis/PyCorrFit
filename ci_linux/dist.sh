#!/bin/bash
# Call this script from the parent directory
docker run --rm -v `pwd`:/io $DOCKER_IMAGE $PRE_CMD /io/travis/build-wheels.sh
mkdir -p dist
mv wheelhouse/*.whl dist/
python setup.py sdist
