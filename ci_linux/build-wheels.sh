#!/bin/bash
set -e -x

cd /io

# Test 
for PYBIN in /opt/python/cp27*/bin/; do
    "${PYBIN}/pip" install --upgrade pip
    "${PYBIN}/pip" install -e .
    "${PYBIN}/python" setup.py develop
    "${PYBIN}/python" setup.py test
done

# Compile wheels
for PYBIN in /opt/python/cp27*/bin; do
    "${PYBIN}/python" setup.py develop
    "${PYBIN}/pip" wheel . -w dist/
done

# Bundle external shared libraries into the wheels
for whl in /io/dist/*.whl; do
    auditwheel repair "$whl" -w /io/dist/
done


