#!/bin/bash
set -e -x

cd /io

for PYBIN in /opt/python/cp${TRAVIS_PYTHON_VERSION//./}*/bin/; do
    # Install
    "${PYBIN}/pip" install -e .
    "${PYBIN}/python" setup.py build_ext --inplace --force
    # Test
    "${PYBIN}/python" setup.py test
    # Wheels
    "${PYBIN}/pip" wheel /io/ -w wheelhouse/ --no-deps
    rm -rf .eggs
done

# Bundle external shared libraries into the wheels
for whl in /io/wheelhouse/*.whl; do
    auditwheel repair "$whl" -w /io/dist/
done


