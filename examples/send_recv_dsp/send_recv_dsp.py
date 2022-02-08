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
import argparse

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from qubelib import *

SAVE_DIR = "result_send_recv_dsp/"
IP_ADDR = '10.0.0.16'
CAPTURE_DELAY = 100
NUM_WAVE_CYCLES = 512
NUM_WAVE_SEQ_REPEATS = 16

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
    dt = 2.0 * math.pi * (freq * 1e6) / AwgCtrl.SAMPLING_RATE
    num_samples = int(num_cycles * AwgCtrl.SAMPLING_RATE / (freq * 1e6))
    i_data =  [int(amp * math.cos(i * dt)) for i in range(num_samples)]
    q_data =  [int(amp * math.sin(i * dt)) for i in range(num_samples)]
    return list(zip(i_data, q_data))


def gen_wave_seq():
    wave_seq = WaveSequence(
        num_wait_words = 16,
        num_repeats = NUM_WAVE_SEQ_REPEATS)

    num_chunks = 1
    samples = gen_cos_wave(4.8, NUM_WAVE_CYCLES, 32760)
    for i in range(num_chunks):
        # 1 波形チャンクのサンプル数は 64 の倍数でなければならない
        num_samples_in_wblcok = WaveSequence.NUM_SAMPLES_IN_WAVE_BLOCK
        if len(samples) % num_samples_in_wblcok != 0:
            additional_samples = num_samples_in_wblcok - (len(samples) % num_samples_in_wblcok)
            samples.extend([(0, 0)] * additional_samples)

        wave_seq.add_chunk(
            iq_samples = samples, # 50MHz cos x512
            num_blank_words = 0, 
            num_repeats = 1)
    return wave_seq


def set_wave_sequence(awg_ctrl):
    awg_to_wave_sequence = {}
    for awg_id in AWG.all():
        wave_seq = gen_wave_seq()
        awg_to_wave_sequence[awg_id] = wave_seq
        awg_ctrl.set_wave_seqeuence(awg_id, wave_seq)
    return awg_to_wave_sequence


def set_capture_params(cap_ctrl, wave_seq):
    capture_param = gen_capture_param(wave_seq)
    for captu_unit_id in CaptureUnit.all():
        cap_ctrl.set_capture_params(captu_unit_id, capture_param)


def gen_capture_param(wave_seq):
    capture_param = CaptureParam()
    capture_param.num_integ_sections = wave_seq.num_repeats

    num_sum_sections = NUM_WAVE_CYCLES * 2 
    wave_words = (wave_seq.num_all_words -  wave_seq.num_wait_words)
    sum_section_len = wave_words // wave_seq.num_repeats // num_sum_sections  # 出力する余弦波の半周期分を総和区間とする
    for _ in range(num_sum_sections):
        # 総和区間長が 6 ワード以下の場合 decimation から値が出てこなくなるので 7 ワード以上を指定する
        capture_param.add_sum_section(sum_section_len - 1, 1)
    # 総和範囲の指定
    capture_param.sum_start_word_no = 0
    capture_param.num_words_to_sum = CaptureParam.MAX_SUM_SECTION_LEN

    capture_param.sel_dsp_units_to_enable(*DspUnit.all())
    capture_param.complex_fir_coefs = [1 + 0j] + [0] * (CaptureParam.NUM_COMPLEX_FIR_COEFS - 1)
    capture_param.real_fir_i_coefs = [1] + [0] * (CaptureParam.NUM_REAL_FIR_COEFS - 1)
    capture_param.real_fir_q_coefs = capture_param.real_fir_i_coefs
    capture_param.complex_window_coefs = [1 + 0j] * CaptureParam.NUM_COMPLEXW_WINDOW_COEFS
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


def main():

    awg_ctrl = AwgCtrl(IP_ADDR)
    cap_ctrl = CaptureCtrl(IP_ADDR)
    # 初期化
    init_modules(awg_ctrl, cap_ctrl)
    # トリガ AWG の設定
    set_trigger_awg(cap_ctrl)
    # 波形シーケンスの設定
    awg_to_wave_sequence = set_wave_sequence(awg_ctrl)
    # キャプチャパラメータの設定
    set_capture_params(cap_ctrl, awg_to_wave_sequence[AWG.U0])
    # 波形送信スタート
    awg_ctrl.start_awgs()
    # 波形送信完了待ち
    awg_ctrl.wait_for_awgs_to_stop(5, *AWG.all())
    # キャプチャ完了待ち
    cap_ctrl.wait_for_capture_units_to_stop(5, *CaptureUnit.all())
    # キャプチャデータ取得
    capture_unit_to_capture_data = get_capture_data(cap_ctrl)

    # 波形保存
    #awg_to_wave_data = {awg: wave_seq.all_samples(False) for awg, wave_seq in awg_to_wave_sequence.items()}
    #save_sample_data('awg', AwgCtrl.SAMPLING_RATE, awg_to_wave_data) # 時間がかかるので削除
    save_sample_data('capture', CaptureCtrl.SAMPLING_RATE, capture_unit_to_capture_data)
    print('end')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr')
    args = parser.parse_args()
    if args.ipaddr is not None:
        IP_ADDR = args.ipaddr

    main()
