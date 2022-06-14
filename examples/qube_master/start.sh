#!/bin/sh

python3 qubemasterclient.py --ipaddr=10.3.0.255 --command=start
python3 qubemasterclient.py --ipaddr=10.3.0.255 --command=kick
