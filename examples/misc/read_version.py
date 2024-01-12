# デバッグ用スクリプト
import sys

import argparse
from e7awgsw import AwgCtrl, CaptureCtrl, SequencerCtrl

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr1')
    parser.add_argument('--ipaddr2')
    args = parser.parse_args()
    
    if args.ipaddr1 is None or args.ipaddr2 is None:
        print(f"Usage: {sys.argv[0]} --ipaddr1=ADDRESS1 --ipaddr2=ADDRESS2")
        exit(0)

    addr1 = args.ipaddr1
    addr2 = args.ipaddr2

    print("AWG Version", AwgCtrl(addr1).version())
    print("Capture Version", CaptureCtrl(addr1).version())

    ctrl = SequencerCtrl(addr2)
    ctrl.initialize()
    print("Sequencer Version", ctrl.version())
    ctrl.close()

