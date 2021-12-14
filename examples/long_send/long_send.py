"""
AWG から 50MHz の余弦波を出力して, 信号処理モジュールを全て無効にしてキャプチャします.
"""
import sys
import pathlib
import math
import argparse

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from qubelib import *

IP_ADDR = '10.0.0.16'

def init_modules(awg_ctrl, cap_ctrl):
    awg_ctrl.initialize()
    awg_ctrl.enable_awgs(*AWG.all())
    cap_ctrl.initialize()

def gen_wave_seq(freq):
    wave_seq = WaveSequence(
        num_wait_words = 16,
        num_repeats = 0xFFFFFFFF)
    
    num_chunks = 1
    for _ in range(num_chunks):
        i_wave = SinWave(num_cycles = 8, frequency = freq, amplitude = 32760, phase = math.pi / 2)
        q_wave = SinWave(num_cycles = 8, frequency = freq, amplitude = 32760)
        iq_samples = IqWave(i_wave, q_wave).gen_samples(
            sampling_rate = AwgCtrl.SAMPLING_RATE, 
            padding_size = WaveSequence.NUM_SAMPLES_IN_WAVE_BLOCK)

        wave_seq.add_chunk(
            iq_samples = iq_samples,
            num_blank_words = 0, 
            num_repeats = 0xFFFFFFFF)
    return wave_seq

def set_wave_sequence(awg_ctrl):
    awg_to_wave_sequence = {}
    for awg_id in AWG.all():
        wave_seq = gen_wave_seq(5e6) # 5 MHz
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
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr')
    args = parser.parse_args()
    if args.ipaddr is not None:
        IP_ADDR = args.ipaddr

    main()
