"""
AWG の WAIT WORD (波形シーケンスの先頭に付く 0 データの長さ) を指定して波形を出力する.
"""
import sys
import os
import pathlib
import math
import argparse

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from qubelib import *

IP_ADDR = '10.0.0.16'
CAPTURE_DELAY = 0
SAVE_DIR = "result_wait_word/"

def init_modules(awg_ctrl, cap_ctrl):
    awg_ctrl.initialize()
    awg_ctrl.enable_awgs(*AWG.all())
    cap_ctrl.initialize()
    cap_ctrl.enable_capture_units(*CaptureUnit.all())


def set_trigger_awg(cap_ctrl):
    cap_ctrl.select_trigger_awg(CaptureModule.U0, AWG.U0)
    cap_ctrl.select_trigger_awg(CaptureModule.U1, AWG.U1)


def gen_cos_wave(freq, num_cycles, amp):
    """
    freq : MHz
    """
    i_wave = SinWave(num_cycles = num_cycles, frequency = freq, amplitude = amp, phase = math.pi / 2)
    q_wave = SinWave(num_cycles = num_cycles, frequency = freq, amplitude = amp)
    return IqWave(i_wave, q_wave).gen_samples(
        sampling_rate = AwgCtrl.SAMPLING_RATE, 
        padding_size = WaveSequence.NUM_SAMPLES_IN_WAVE_BLOCK)

def gen_wave_seq(shift):
    samples = gen_cos_wave(4e6, 8, 32760)
    num_wait_words = 16 + int(len(samples) * shift / WaveSequence.NUM_SAMPLES_IN_AWG_WORD)
    wave_seq = WaveSequence(
        num_wait_words = num_wait_words,
        num_repeats = 1)
    wave_seq.add_chunk(
        iq_samples = samples,
        num_blank_words = 0, 
        num_repeats = 1)
    return wave_seq


def set_wave_sequence(awg_ctrl):
    awg_to_wave_sequence = {}
    for awg_id in AWG.all():
        wave_seq = gen_wave_seq(awg_id / 8)
        awg_to_wave_sequence[awg_id] = wave_seq
        awg_ctrl.set_wave_seqeuence(awg_id, wave_seq)
    return awg_to_wave_sequence


def set_capture_params(cap_ctrl, num_capture_words):
    capture_param = gen_capture_param(num_capture_words)
    for captu_unit_id in CaptureUnit.all():
        cap_ctrl.set_capture_params(captu_unit_id, capture_param)


def gen_capture_param(num_capture_words):
    capture_param = CaptureParam()
    capture_param.num_integ_sections = 1
    capture_param.add_sum_section(num_capture_words, 1) # 総和区間を 1 つだけ定義する
    capture_param.capture_delay = CAPTURE_DELAY
    return capture_param

def get_capture_data(cap_ctrl):
    capture_unit_to_capture_data = {}
    for capture_unit_id in CaptureUnit.all():
        num_captured_samples = cap_ctrl.num_captured_samples(capture_unit_id)
        capture_unit_to_capture_data[capture_unit_id] = cap_ctrl.get_capture_data(capture_unit_id, num_captured_samples)
    return capture_unit_to_capture_data

def save_sample_data(prefix, sampling_rate, id_to_samples):
    for id, samples in id_to_samples.items():
        dir = SAVE_DIR + '/{}_{}'.format(prefix, id)
        os.makedirs(dir, exist_ok = True)
        print('save {} {} data'.format(prefix, id))

        # I/Q データテキストファイル保存
        filepath = dir + '/{}_{}.txt'.format(prefix, id)
        with open(filepath, 'w') as txt_file:
            for i_data, q_data in samples:
                txt_file.write("{}  ,  {}\n".format(i_data, q_data))

        # I データグラフ保存
        i_data = [sample[0] for sample in samples]
        plot_graph(
            sampling_rate, 
            i_data, 
            '{}_{}_I'.format(prefix, id), 
            dir + '/{}_{}_I.png'.format(prefix, id),
            '#b44c97')

        # Q データグラフ保存
        q_data = [sample[1] for sample in samples]
        plot_graph(
            sampling_rate,
            q_data, 
            '{}_{}_Q'.format(prefix, id), 
            dir + '/{}_{}_Q.png'.format(prefix, id),
            '#00a497')

def check_err(awg_ctrl, cap_ctrl):
    awg_to_err = awg_ctrl.check_err(*AWG.all())
    for awg_id, err_list in awg_to_err.items():
        print(awg_id)
        for err in err_list:
            print('    {}'.format(err))
    
    cap_unit_to_err = cap_ctrl.check_err(*CaptureUnit.all())
    for cap_unit_id, err_list in cap_unit_to_err.items():
        print('{} err'.format(cap_unit_id))
        for err in err_list:
            print('    {}'.format(err))


def main():
    awg_ctrl = AwgCtrl(IP_ADDR)
    cap_ctrl = CaptureCtrl(IP_ADDR)
    # 初期化
    init_modules(awg_ctrl, cap_ctrl)
    # トリガ AWG の設定
    set_trigger_awg(cap_ctrl)
    # 波形シーケンスの設定
    awg_to_wave_sequence = set_wave_sequence(awg_ctrl)
    # 最大波形シーケンス長の特定
    max_wave_seq_len = max([wave_seq.num_all_words for awg_id, wave_seq in awg_to_wave_sequence.items()])
    # キャプチャパラメータの設定
    set_capture_params(cap_ctrl, max_wave_seq_len)
    # 波形送信スタート
    awg_ctrl.start_awgs()
    # 波形送信完了待ち
    awg_ctrl.wait_for_awgs_to_stop(5, *AWG.all())
    # キャプチャ完了待ち
    cap_ctrl.wait_for_capture_units_to_stop(5, *CaptureUnit.all())
    # エラーチェック
    check_err(awg_ctrl, cap_ctrl)
    # キャプチャデータ取得
    capture_unit_to_capture_data = get_capture_data(cap_ctrl)
    # 波形保存
    awg_to_wave_data = {awg: wave_seq.all_samples(True) for awg, wave_seq in awg_to_wave_sequence.items()}
    save_sample_data('awg', AwgCtrl.SAMPLING_RATE, awg_to_wave_data)
    save_sample_data('capture', CaptureCtrl.SAMPLING_RATE, capture_unit_to_capture_data)
    print('end')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr')
    args = parser.parse_args()
    if args.ipaddr is not None:
        IP_ADDR = args.ipaddr

    main()