"""
AWG から 4.8MHz の余弦波を出力して, 信号処理モジュールを全て有効にしてキャプチャします.
フィルタおよび窓関数の係数の設定方法は, gen_capture_param() を参照してください.

総和区間 = 12 キャプチャワード
総和区間数 = 1024
積算回数 = 16

"""
import sys
import os
import pathlib
import math

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
    try:
        mode = int(sys.argv[1])
    except Exception:
        mode = 0
    main(mode)
