import sys
import pathlib
import argparse

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from qubelib import *

IP_ADDR = '10.0.0.16'

def init_modules(awg_ctrl, cap_ctrl):
    awg_ctrl.initialize()
    awg_ctrl.enable_awgs(*AWG.all())
    cap_ctrl.initialize()
    cap_ctrl.enable_capture_units(*CaptureUnit.all())

def main(mode):   
    awg_ctrl = AwgCtrl(IP_ADDR)
    cap_ctrl = CaptureCtrl(IP_ADDR)
    
    if mode == 0:
        # AWG およびキャプチャモジュールのリセット
        awg_ctrl.reset_awgs(*AWG.all())
        cap_ctrl.reset_capture_units(*CaptureUnit.all())
    else:
        # AWG およびキャプチャモジュールのリセット + コントロールレジスタの初期化
        init_modules(awg_ctrl, cap_ctrl)

    print('end')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('mode')
    parser.add_argument('--ipaddr')
    args = parser.parse_args()
    if args.ipaddr is not None:
        IP_ADDR = args.ipaddr
    try:
        mode = int(args.mode)
    except Exception:
        mode = 0

    main(mode)
