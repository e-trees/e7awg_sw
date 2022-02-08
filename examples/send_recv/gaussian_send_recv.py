"""
プログラム引数で指定した AWG からガウスパルスを出力して, 信号処理モジュールを全て無効にしてキャプチャします.
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
SAVE_DIR = "result_gaussian_send_recv/"

def init_modules(awg_ctrl, cap_ctrl, awg_id):
    awg_ctrl.initialize()
    awg_ctrl.enable_awgs(awg_id)
    cap_ctrl.initialize()
    cap_ctrl.enable_capture_units(*CaptureUnit.all())


def set_trigger_awg(cap_ctrl, awg_id):
    cap_ctrl.select_trigger_awg(CaptureModule.U0, awg_id)
    cap_ctrl.select_trigger_awg(CaptureModule.U1, awg_id)


def gen_wave_seq():
    wave_seq = WaveSequence(
        num_wait_words = 16,
        num_repeats = 1)
    
    num_chunks = 1
    for i in range(num_chunks):
        i_wave = GaussianPulse(num_cycles = 1, frequency = 2e6, amplitude = 20000, duration = 6.0, variance = 0.4)
        q_wave = SquareWave(num_cycles = 1, frequency = 2e6, amplitude = 0, duty_cycle = 0.0)
        iq_samples = IqWave(i_wave, q_wave).gen_samples(
            sampling_rate = AwgCtrl.SAMPLING_RATE, 
            padding_size = WaveSequence.NUM_SAMPLES_IN_WAVE_BLOCK)

        wave_seq.add_chunk(
            iq_samples = iq_samples,
            num_blank_words = 0, 
            num_repeats = 1)
    return wave_seq


def set_wave_sequence(awg_ctrl, awg_id):
    wave_seq = gen_wave_seq()
    awg_ctrl.set_wave_seqeuence(awg_id, wave_seq)
    return wave_seq


def set_capture_params(cap_ctrl, wave_seq):
    capture_param = gen_capture_param(wave_seq)
    for captu_unit_id in CaptureUnit.all():
        cap_ctrl.set_capture_params(captu_unit_id, capture_param)


def gen_capture_param(wave_seq):
    capture_param = CaptureParam()
    capture_param.num_integ_sections = 1
    capture_param.add_sum_section(wave_seq.num_all_words - wave_seq.num_wait_words, 1) # 総和区間を 1 つだけ定義する
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


def main(awg_id):
    awg_ctrl = AwgCtrl(IP_ADDR)
    cap_ctrl = CaptureCtrl(IP_ADDR)
    # 初期化
    init_modules(awg_ctrl, cap_ctrl, awg_id)
    # トリガ AWG の設定
    set_trigger_awg(cap_ctrl, awg_id)
    # 波形シーケンスの設定
    wave_seq = set_wave_sequence(awg_ctrl, awg_id)
    # キャプチャパラメータの設定
    set_capture_params(cap_ctrl, wave_seq)
    # 波形送信スタート
    awg_ctrl.start_awgs()
    # 波形送信完了待ち
    awg_ctrl.wait_for_awgs_to_stop(5, awg_id)
    # キャプチャ完了待ち
    cap_ctrl.wait_for_capture_units_to_stop(5, *CaptureUnit.all())
    # エラーチェック
    check_err(awg_ctrl, cap_ctrl)
    # キャプチャデータ取得
    capture_unit_to_capture_data = get_capture_data(cap_ctrl)
    # 波形保存
    awg_to_wave_data = { awg_id: wave_seq.all_samples(False) }
    save_sample_data('awg', AwgCtrl.SAMPLING_RATE, awg_to_wave_data)
    save_sample_data('capture', CaptureCtrl.SAMPLING_RATE, capture_unit_to_capture_data)
    print('end')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr')
    parser.add_argument('--awg')
    args = parser.parse_args()

    if args.ipaddr is not None:
        IP_ADDR = args.ipaddr

    awg_id = AWG.U0
    if args.awg is not None:
        awg_id = AWG.of(int(args.awg))

    main(awg_id)
