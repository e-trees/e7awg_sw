"""
AWG から 50MHz の余弦波を出力して, 信号処理モジュールを全て無効にしてキャプチャします.
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

def gen_cos_wave(freq, num_cycles, amp):
    """
    freq : MHz
    """
    dt = 2.0 * math.pi * (freq * 1e6) / AwgCtrl.SAMPLING_RATE
    num_samples = int(num_cycles * AwgCtrl.SAMPLING_RATE / (freq * 1e6))
    i_data =  [int(amp * math.cos(i * dt)) for i in range(num_samples)]
    q_data =  [int(amp * math.sin(i * dt)) for i in range(num_samples)]
    return list(zip(i_data, q_data))

def gen_wave_seq():
    wave_seq = WaveSequence(
        num_wait_words = 16,
        num_repeats = 0xFFFFFFFF)
    
    num_chunks = 1
    for i in range(num_chunks):
        samples = gen_cos_wave(50, 8, 32760)
        # 1 波形チャンクのサンプル数は 64 の倍数でなければならない
        num_samples_in_wblock = WaveSequence.NUM_SAMPLES_IN_WAVE_BLOCK
        if len(samples) % num_samples_in_wblock != 0:
            additional_samples = num_samples_in_wblock - (len(samples) % num_samples_in_wblock)
            samples.extend([(0, 0)] * additional_samples)
        wave_seq.add_chunk(
            iq_samples = samples, # 50MHz cos x2
            num_blank_words = 0, 
            num_repeats = 0xFFFFFFFF)
    return wave_seq


def set_wave_sequence(awg_ctrl):
    awg_to_wave_sequence = {}
    for awg_id in AWG.all():
        wave_seq = gen_wave_seq()
        awg_to_wave_sequence[awg_id] = wave_seq
        awg_ctrl.set_wave_seqeuence(awg_id, wave_seq)
    return awg_to_wave_sequence


def main():
    awg_ctrl = AwgCtrl(IP_ADDR)
    cap_ctrl = CaptureCtrl(IP_ADDR)
    # 初期化
    init_modules(awg_ctrl, cap_ctrl)
    # 波形シーケンスの設定
    awg_to_wave_sequence = set_wave_sequence(awg_ctrl)
    # 波形送信スタート
    awg_ctrl.start_awgs()
    print('end')


if __name__ == "__main__":
    main()
