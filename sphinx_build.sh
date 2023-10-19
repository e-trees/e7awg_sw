#!/bin/bash

set -eu

cd "$(dirname $0)"

rm -rf ./docs/_build
mkdir ./docs/_build
rm -f ./docs/*.rst
cat > docs/index.rst <<EOS
.. e7awg Software Library documentation master file, created by
   sphinx-quickstart on Thu Oct 14 16:04:23 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root \`toctree\` directive.

e7awg Software Library's documentation
===============================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   e7awgsw

Indices and tables
==================

* :ref:\`genindex\`
* :ref:\`modindex\`
* :ref:\`search\`
EOS
sphinx-apidoc --module-first -f  --implicit-namespaces -o ./docs ./e7awgsw/ ./e7awgsw/__init__.py \
./e7awgsw/feedback/memorymap.py ./e7awgsw/feedback/udpaccess.py ./e7awgsw/feedback/uplpacket.py \
./e7awgsw/feedback/hwparam.py ./e7awgsw/feedback/logger.py ./e7awgsw/feedback/classification.py \
./e7awgsw/feedback/lock.py ./e7awgsw/feedback/dspmodule.py \
./e7awgsw/simplemulti/memorymap.py ./e7awgsw/simplemulti/udpaccess.py ./e7awgsw/simplemulti/uplpacket.py \
./e7awgsw/simplemulti/hwparam.py ./e7awgsw/simplemulti/logger.py ./e7awgsw/simplemulti/classification.py \
./e7awgsw/simplemulti/lock.py ./e7awgsw/simplemulti/dspmodule.py
sphinx-build ./docs ./docs/_build


