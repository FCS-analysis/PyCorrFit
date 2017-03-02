#!/bin/bash
set -e -x

# Test 
for PYBIN in /opt/python/cp27*/bin/; do
    "${PYBIN}/python" /io/setup.py develop
    "${PYBIN}/python" /io/setup.py test
    "${PYBIN}/python" /io/setup.py clean
done

# Compile wheels
for PYBIN in /opt/python/cp27*/bin; do
    "${PYBIN}/pip" install -e /io
    "${PYBIN}/python" /io/setup.py develop
    "${PYBIN}/pip" wheel /io/ -w dist/
done

# Bundle external shared libraries into the wheels
for whl in dist/*.whl; do
    auditwheel repair "$whl" -w /io/dist/
done


