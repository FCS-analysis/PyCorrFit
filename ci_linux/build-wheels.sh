#!/bin/bash
set -e -x

# Compile wheels
for PYBIN in /opt/python/*/bin; do
    "${PYBIN}/pip" install -e /io
    "${PYBIN}/pip" wheel /io/ -w dist/
done

# Bundle external shared libraries into the wheels
for whl in dist/*.whl; do
    auditwheel repair "$whl" -w /io/dist/
done

# Install packages and test
for PYBIN in /opt/python/*/bin/; do
    "${PYBIN}/python" install pycorrfit --no-index -f /io/dist
#    cd "$HOME"
#    
#    (; "${PYBIN}/python" pymanylinuxdemo)
done
