from __future__ import annotations

import os
import argparse
import capture
from typing import Final
from awg import Awg
from hbm import Hbm
from awgcontroller import AwgController
from collections.abc import Sequence, Mapping
from capturecontroller import CaptureController
from upldispatcher import UplDispatcher
from e7awgsw import CaptureUnit, CaptureModule, AWG

CAPTURE_START_DELAY: Final = 31 # キャプチャスタートからキャプチャディレイをカウントし始めるまでの準備時間 (単位 : ワード)

# AWG とキャプチャモジュールのデータバスの接続関係
awg_to_capture_module = {
    AWG.U2  : CaptureModule.U0,
    AWG.U15 : CaptureModule.U1,
    AWG.U3  : CaptureModule.U2,
    AWG.U4  : CaptureModule.U3
}


def on_wave_generated(
    awg_id_to_wave: Mapping[AWG, Sequence[tuple[int, int]]],
    cap_ctrl: CaptureController
) -> None:
    """AWG が起動したときのイベントハンドラ"""
    cap_mod_to_wave: dict[CaptureModule, Sequence[tuple[int, int]]] = {
        CaptureModule.U0: [],
        CaptureModule.U1: [],
        CaptureModule.U2: [],
        CaptureModule.U3: []
    }
    for awg_id, wave in awg_id_to_wave.items():
        cap_mod = awg_to_capture_module.get(awg_id)
        if cap_mod is not None:
            cap_mod_to_wave[cap_mod] = wave # キャプチャモジュールに入力される波形データを AWG が出力したものに変更
    cap_ctrl.on_wave_generated(awg_id_to_wave.keys(), cap_mod_to_wave)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr', default='0.0.0.0')
    args = parser.parse_args()

    hbm = Hbm(0x200000000)
    cap_ctrl = CaptureController()
    for cap_unit_id in CaptureUnit.all():
        cap_unit = capture.CaptureUnit(cap_unit_id, hbm.write, CAPTURE_START_DELAY)
        cap_ctrl.add_capture_unit(cap_unit)

    awg_ctrl = AwgController()
    awg_ctrl.add_on_wave_generated(
        lambda awg_id_to_wave : on_wave_generated(awg_id_to_wave, cap_ctrl))
    for awg_id in AWG.all():
        awg = Awg(awg_id, hbm.read)
        awg_ctrl.add_awg(awg)

    upl_dispatcher = UplDispatcher(args.ipaddr, hbm, awg_ctrl, cap_ctrl)
    upl_dispatcher.start()

    print('The emulator has been started.')
    input("Press 'Enter' to stop\n")
    os._exit(0)
