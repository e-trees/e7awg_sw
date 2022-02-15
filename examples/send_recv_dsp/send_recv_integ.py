"""
AWG から control 波形と readout 波形を出力して, 積算処理モジュールを有効にしてキャプチャします.
"""
import sys
import os
import pathlib
import math
import argparse
from collections import namedtuple

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from qubelib import *

SAVE_DIR = "result_send_recv_integ/"
IP_ADDR = '10.0.0.16'
CAPTURE_DELAY = 100 # cpature words = cycyles@125MHz 

wave_params = namedtuple(
    'WaveParams',
    ('num_wait_words',
     'ctrl_freq',
     'ctrl_wave_len',
     'readout_freq',
     'readout_wave_len',
     'num_readout_blank',
     'num_chunk_repeats'))

awg_list = namedtuple(
    'AwgList',
    ('ctrl_awg_0',
     'ctrl_awg_1',
     'readout_awg_0',
     'readout_awg_1'))

AWG_LIST = awg_list(
    ctrl_awg_0 = AWG.U0,
    ctrl_awg_1 = AWG.U2,
    readout_awg_0 = AWG.U13,
    readout_awg_1 = AWG.U15
)

def init_modules(awg_ctrl, cap_ctrl, capture_units):
    awg_ctrl.initialize()
    awg_ctrl.enable_awgs(*AWG_LIST)
    cap_ctrl.initialize()
    cap_ctrl.enable_capture_units(*capture_units)


def set_trigger_awg(cap_ctrl, capture_modules):
    if CaptureModule.U0 in capture_modules:
        cap_ctrl.select_trigger_awg(CaptureModule.U0, AWG_LIST.ctrl_awg_0)
    if CaptureModule.U1 in capture_modules:
        cap_ctrl.select_trigger_awg(CaptureModule.U1, AWG_LIST.ctrl_awg_1)


def gen_cos_wave(freq, num_cycles, amp, sampling_rate):
    """
    freq : MHz
    """
    freq = freq * 1e6
    i_samples = SinWave(num_cycles = num_cycles, frequency = freq, amplitude = amp, phase = math.pi / 2).gen_samples(sampling_rate)
    q_samples = SinWave(num_cycles = num_cycles, frequency = freq, amplitude = amp).gen_samples(sampling_rate)
    return (i_samples, q_samples)


def gen_ctrl_wave_samples(params):
    """
    control 波形サンプル作成
    """
    num_cycles = params.ctrl_freq * params.ctrl_wave_len * 1e-3
    return gen_cos_wave(params.ctrl_freq, num_cycles, 32760, AwgCtrl.SAMPLING_RATE)

def gen_readout_wave_samples(params, num_pre_blank_samples):
    """
    readout 波形サンプル作成
    """
    num_cycles = params.readout_freq * params.readout_wave_len * 1e-3
    i_samples, q_samples = gen_cos_wave(params.readout_freq, num_cycles, 32760, AwgCtrl.SAMPLING_RATE)
    i_samples = [0] * num_pre_blank_samples + i_samples
    q_samples = [0] * num_pre_blank_samples + q_samples
    return (i_samples, q_samples)


def gen_ctrl_wave_seq(params, num_all_samples, i_samples, q_samples):
    """
    control 波形シーケンス作成
    """
    iq_samples = IqWave.convert_to_iq_format(i_samples, q_samples, WaveSequence.NUM_SAMPLES_IN_WAVE_BLOCK)
    num_blank_samples = num_all_samples - len(iq_samples)
    num_blank_words = num_blank_samples // WaveSequence.NUM_SAMPLES_IN_AWG_WORD

    wave_seq = WaveSequence(num_wait_words = params.num_wait_words, num_repeats = 1)
    wave_seq.add_chunk(
        iq_samples = iq_samples,
        num_blank_words = num_blank_words, 
        num_repeats = params.num_chunk_repeats
    )
    return wave_seq


def gen_readout_wave_seq(params, i_samples, q_samples):
    """
    readout 波形シーケンス作成
    """
    iq_samples = IqWave.convert_to_iq_format(i_samples, q_samples, WaveSequence.NUM_SAMPLES_IN_WAVE_BLOCK)
    num_added_samples = len(iq_samples) - len(i_samples) # 付加された 0 データは, ブランク波形の一部とする
    num_blank_samples = max(
        int(AwgCtrl.SAMPLING_RATE * params.num_readout_blank / 1e3) - num_added_samples, 0)
    num_blank_words = num_blank_samples // WaveSequence.NUM_SAMPLES_IN_AWG_WORD

    wave_seq = WaveSequence(num_wait_words = params.num_wait_words, num_repeats = 1)
    wave_seq.add_chunk(
        iq_samples = iq_samples,
        num_blank_words = num_blank_words, 
        num_repeats = params.num_chunk_repeats
    )
    return wave_seq


def set_wave_sequence(awg_ctrl, params):
    # サンプル作成
    ctrl_i_samples, ctrl_q_samples = gen_ctrl_wave_samples(params)
    ro_i_samples, ro_q_samples = gen_readout_wave_samples(params, len(ctrl_i_samples))

    # 波形シーケンス作成
    ro_wave_seq = gen_readout_wave_seq(params, ro_i_samples, ro_q_samples)
    ctrl_wave_seq = gen_ctrl_wave_seq(
        params, ro_wave_seq.chunk(0).num_samples, ctrl_i_samples, ctrl_q_samples)

    # control 波形と readout 波形の長さが一致することを確認
    assert ctrl_wave_seq.num_all_words == ro_wave_seq.num_all_words

    awg_ctrl.set_wave_sequence(AWG_LIST.ctrl_awg_0, ctrl_wave_seq)
    awg_ctrl.set_wave_sequence(AWG_LIST.ctrl_awg_1, ctrl_wave_seq)
    awg_ctrl.set_wave_sequence(AWG_LIST.readout_awg_0, ro_wave_seq)
    awg_ctrl.set_wave_sequence(AWG_LIST.readout_awg_1, ro_wave_seq)
    return {
        AWG_LIST.ctrl_awg_0 : ctrl_wave_seq,
        AWG_LIST.ctrl_awg_1 : ctrl_wave_seq,
        AWG_LIST.readout_awg_0 : ro_wave_seq,
        AWG_LIST.readout_awg_1 : ro_wave_seq
    }


def set_capture_params(cap_ctrl, wave_seq, capture_units):
    capture_param = gen_capture_param(wave_seq)
    for captu_unit_id in capture_units:
        cap_ctrl.set_capture_params(captu_unit_id, capture_param)


def gen_capture_param(wave_seq):
    capture_param = CaptureParam()
    capture_param.num_integ_sections = wave_seq.chunk(0).num_repeats # 積算区間数

    # readout 波形の長さから, 追加で 1us キャプチャするためのキャプチャワード数を計算
    additional_capture_words = int(1e-6 * CaptureCtrl.SAMPLING_RATE) // CaptureParam.NUM_SAMPLES_IN_ADC_WORD
    additional_capture_words = min(additional_capture_words, wave_seq.chunk(0).num_blank_words - 1)

    sum_section_len = wave_seq.chunk(0).num_words - wave_seq.chunk(0).num_blank_words + additional_capture_words
    num_blank_words = wave_seq.chunk(0).num_words - sum_section_len
    capture_param.add_sum_section(sum_section_len, num_blank_words)
    capture_param.sum_start_word_no = 0
    capture_param.num_words_to_sum = CaptureParam.MAX_SUM_SECTION_LEN
    capture_param.sel_dsp_units_to_enable(DspUnit.INTEGRATION)
    capture_param.capture_delay = CAPTURE_DELAY
    # readout 波形のサンプル数とキャプチャするサンプル数が一致することを確認
    assert wave_seq.num_all_samples == capture_param.num_samples_to_process
    return capture_param


def get_capture_data(cap_ctrl, capture_units):
    capture_unit_to_capture_data = {}
    for capture_unit_id in capture_units:
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


def check_err(awg_ctrl, cap_ctrl, awgs, capture_units):
    awg_to_err = awg_ctrl.check_err(*awgs)
    for awg_id, err_list in awg_to_err.items():
        print(awg_id)
        for err in err_list:
            print('    {}'.format(err))
    
    cap_unit_to_err = cap_ctrl.check_err(*capture_units)
    for cap_unit_id, err_list in cap_unit_to_err.items():
        print('{} err'.format(cap_unit_id))
        for err in err_list:
            print('    {}'.format(err))


def main(wave_params, capture_modules):
    awg_ctrl = AwgCtrl(IP_ADDR)
    cap_ctrl = CaptureCtrl(IP_ADDR)
    capture_units = CaptureModule.get_units(*capture_modules)
    # 初期化
    init_modules(awg_ctrl, cap_ctrl, capture_units)
    # トリガ AWG の設定
    set_trigger_awg(cap_ctrl, capture_modules)
    # 波形シーケンスの設定
    awg_to_wave_sequence = set_wave_sequence(awg_ctrl, wave_params)
    # キャプチャパラメータの設定
    set_capture_params(cap_ctrl, awg_to_wave_sequence[AWG_LIST.readout_awg_0], capture_units)
    # 波形送信スタート
    awg_ctrl.start_awgs()
    # 波形送信完了待ち
    awg_ctrl.wait_for_awgs_to_stop(5, *AWG_LIST)
    # キャプチャ完了待ち
    cap_ctrl.wait_for_capture_units_to_stop(5, *capture_units)
    # エラーチェック
    check_err(awg_ctrl, cap_ctrl, AWG_LIST, capture_units)
    # キャプチャデータ取得
    capture_unit_to_capture_data = get_capture_data(cap_ctrl, capture_units)

    # 波形保存
    # awg_to_wave_data = {awg: wave_seq.all_samples(False) for awg, wave_seq in awg_to_wave_sequence.items()}
    # save_sample_data('awg', AwgCtrl.SAMPLING_RATE, awg_to_wave_data) # 時間がかかるので削除
    save_sample_data('capture', CaptureCtrl.SAMPLING_RATE, capture_unit_to_capture_data)
    print('end')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr')
    parser.add_argument('--wavelen')
    parser.add_argument('--capture-module')
    args = parser.parse_args()
    
    if args.ipaddr is not None:
        IP_ADDR = args.ipaddr
    
    ctrl_wave_len = 10
    if args.wavelen is not None:
        ctrl_wave_len = int(args.wavelen)

    capture_modules = CaptureModule.all()
    if args.capture_module is not None:
        capture_modules = [CaptureModule.of(int(args.capture_module))]

    wparams = wave_params(
        num_wait_words = 0,
        ctrl_freq = 100, # MHz
        ctrl_wave_len = ctrl_wave_len, # ns
        readout_freq = 100, # MHz,
        readout_wave_len = 2000, # ns,
        num_readout_blank = 0.1, # ms
        num_chunk_repeats = 10000, # 積算回数
    )

    main(wparams, capture_modules)
