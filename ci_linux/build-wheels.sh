#!/bin/bash
set -e -x

# Compile wheels
for PYBIN in /opt/python/cp27*/bin; do
    "${PYBIN}/pip" install -e /io
    "${PYBIN}/pip" wheel /io/ -w dist/
done

# Bundle external shared libraries into the wheels
for whl in dist/*.whl; do
    auditwheel repair "$whl" -w /io/dist/
done

# Test 
for PYBIN in /opt/python/cp27*/bin/; do
    "${PYBIN}/python" setup.py develop    
    "${PYBIN}/python" setup.py test
done
