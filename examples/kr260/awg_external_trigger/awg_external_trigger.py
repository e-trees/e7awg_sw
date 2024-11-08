"""
AWG から余弦波を出力する.
"""
import os
import math
import argparse
import e7awgsw as e7s

# AWG Controller の IP アドレス.
IP_ADDR = '10.0.0.16'

# AWG から出力する余弦波のパラメータ
NUM_FREQ = 1 # MHz
NUM_CYCLES = 4
AMPLITUDE = 30000

def gen_cos_wave(num_cycles, freq, amp, hw_specs):
    """
    freq : MHz
    """
    samples = e7s.SinWave(num_cycles, freq * 1e6, amp, phase = math.pi / 2) \
        .gen_samples(hw_specs.awg.sampling_rate)
    # 波形データに 0 データを足して, その長さを波形パートを構成可能なサンプル数の最小単位の倍数に合わせる.
    reminder = len(samples) % hw_specs.awg.smallest_unit_of_wave_len
    if reminder != 0:
        zeros = [0] * (hw_specs.awg.smallest_unit_of_wave_len - reminder)
        samples.extend(zeros)
    return samples


def gen_cos_wave_seq(num_wait_words, num_chunks, hw_specs):
    wave_seq = e7s.WaveSequence(
        num_wait_words = num_wait_words,
        num_repeats = 1,
        design_type = e7s.E7AwgHwType.KR260)
    i_samples = gen_cos_wave(NUM_CYCLES, NUM_FREQ, AMPLITUDE, hw_specs)
    q_samples = [0] * len(i_samples)
    for _ in range(num_chunks):
        wave_seq.add_chunk(
            iq_samples = list(zip(i_samples, q_samples)),
            num_blank_words = 0,
            num_repeats = 1)
    return wave_seq


def set_wave_sequence(awg_ctrl, awgs, num_wait_words, hw_specs):
    awg_to_wave_sequence = {}
    for awg_id in awgs:
        wave_seq = gen_cos_wave_seq(num_wait_words, 1, hw_specs)
        awg_to_wave_sequence[awg_id] = wave_seq
        awg_ctrl.set_wave_sequence(awg_id, wave_seq)
    return awg_to_wave_sequence


def check_err(awg_ctrl, awgs):
    awg_to_err = awg_ctrl.check_err(*awgs)
    for awg_id, err_list in awg_to_err.items():
        print(awg_id)
        for err in err_list:
            print('    {}'.format(err))


def output_graph(awg_to_wave_seq):
    for awg_id, wave_seq in awg_to_wave_seq.items():
        dirpath = 'plot_send_wave/AWG_{}/'.format(awg_id)
        os.makedirs(dirpath, exist_ok=True)
        samples = wave_seq.all_samples(True)
        e7s.plot_samples(samples, 'waveform', dirpath + "waveform.png")


def main(awgs, num_wait_words, timeout):
    hw_specs = e7s.E7AwgHwSpecs(e7s.E7AwgHwType.KR260)
    with (e7s.AwgCtrl(IP_ADDR, e7s.E7AwgHwType.KR260) as awg_ctrl):
        # 初期化
        awg_ctrl.initialize(*awgs)
        # 波形シーケンスの設定
        awg_to_wave_sequence = set_wave_sequence(awg_ctrl, awgs, num_wait_words, hw_specs)
        # AWG を外部トリガを受け付ける状態にする.
        awg_ctrl.prepare_awgs(*awgs)
        input("Disconnect Pin 27 from Pin 25 on the carrier board and press 'Enter'")
        # 波形送信完了待ち
        awg_ctrl.wait_for_awgs_to_stop(timeout, *awgs)
        # エラーチェック
        check_err(awg_ctrl, awgs)
        # 波形保存
        output_graph(awg_to_wave_sequence)
        print('end')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr')
    parser.add_argument('--awgs')
    parser.add_argument('--num-wait-words', default=0, type=int)
    parser.add_argument('--timeout', default=5, type=int)
    args = parser.parse_args()

    if args.ipaddr is not None:
        IP_ADDR = args.ipaddr

    awgs = sorted(e7s.AWG.on(e7s.E7AwgHwType.KR260))
    if args.awgs is not None:
        awgs = [e7s.AWG(int(x)) for x in args.awgs.split(',')]

    main(awgs, args.num_wait_words, timeout=args.timeout)
