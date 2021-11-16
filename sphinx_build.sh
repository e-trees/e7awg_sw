cd `dirname $0`
rm -rf ./docs/_build
mkdir ./docs/_build
mv ./docs/index.rst .
rm -f ./docs/*.rst
mv ./index.rst ./docs/index.rst
sphinx-apidoc --module-first -f  --implicit-namespaces -o ./docs ./qubelib/ ./qubelib/__init__.py ./qubelib/memorymap.py ./qubelib/udpaccess.py ./qubelib/uplpacket.py ./qubelib/hwparam.py
sphinx-build ./docs ./docs/_build
