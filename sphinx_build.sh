cd `dirname $0`
rm -rf ./docs/_build
mkdir ./docs/_build
mv ./docs/index.rst .
rm -f ./docs/*.rst
mv ./index.rst ./docs/index.rst
sphinx-apidoc --module-first -f  --implicit-namespaces -o ./docs ./e7awgsw/ \
    ./e7awgsw/__init__.py \
    ./e7awgsw/memorymap.py \
    ./e7awgsw/udpaccess.py \
    ./e7awgsw/uplpacket.py \
    ./e7awgsw/hwparam.py \
    ./e7awgsw/logger.py \
    ./e7awgsw/classification.py \
    ./e7awgsw/lock.py \
    ./e7awgsw/dspmodule.py \
    ./e7awgsw/digitaloutput/__init__.py \
    ./e7awgsw/digitaloutput/memorymap.py \
    ./e7awgsw/digitaloutput/doutparam.py \
    ./e7awgsw/zcu111/__init__.py \
    ./e7awgsw/zcu111/rftcmd.py \
    ./e7awgsw/zcu111/rftinterface.py \
    ./e7awgsw/zcu111/rfdcparam.py
    

sphinx-build ./docs ./docs/_build
