# デバッグ用スクリプト
import sys

import argparse
from e7awgsw import AwgCtrl, CaptureCtrl, E7AwgHwType

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr')
    args = parser.parse_args()
    
    if args.ipaddr is None:
        print(f"Usage: {sys.argv[0]} --ipaddr")
        exit(0)

    addr = args.ipaddr

    print("AWG Version", AwgCtrl(addr, E7AwgHwType.SIMPLE_MULTI).version())
    print("Capture Version", CaptureCtrl(addr, E7AwgHwType.SIMPLE_MULTI).version())
