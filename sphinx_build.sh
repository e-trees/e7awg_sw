cd `dirname $0`
rm -rf ./docs/_build
mkdir ./docs/_build
mv ./docs/index.rst .
rm -f ./docs/*.rst
mv ./index.rst ./docs/index.rst
sphinx-apidoc --module-first -f  --implicit-namespaces -o ./docs ./e7awgsw/ ./e7awgsw/__init__.py ./e7awgsw/feedback/memorymap.py ./e7awgsw/feedback/udpaccess.py ./e7awgsw/feedback/uplpacket.py ./e7awgsw/feedback/hwparam.py ./e7awgsw/feedback/logger.py ./e7awgsw/feedback/classification.py ./e7awgsw/feedback/lock.py ./e7awgsw/feedback/dspmodule.py
sphinx-build ./docs ./docs/_build
