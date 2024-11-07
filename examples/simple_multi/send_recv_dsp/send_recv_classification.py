"""
AWG から I = 余弦波, Q = 正弦波を出力して, 四値化モジュールを有効にしてキャプチャします.

総和区間 = 12 キャプチャワード
総和区間数 = 1024
積算回数 = 16

"""
import os
import math
import argparse
import numpy as np
from e7awgsw import DspUnit, CaptureModule, DecisionFunc, AWG, AwgCtrl, \
    CaptureUnit, CaptureCtrl, WaveSequence, CaptureParam, E7AwgHwType
from e7awgsw import SinWave, IqWave, plot_graph
from e7awgsw.labrad import RemoteAwgCtrl, RemoteCaptureCtrl

SAVE_DIR = "result_send_recv_classification/"
IP_ADDR = '10.0.0.16'
CAPTURE_DELAY = 100
NUM_WAVE_CYCLES = 40
NUM_CHUNK_REPEATS = 4
CAP_MOD_TO_UNITS = {
    CaptureModule.U0 : [CaptureUnit.U0, CaptureUnit.U1, CaptureUnit.U2, CaptureUnit.U3],
    CaptureModule.U1 : [CaptureUnit.U4, CaptureUnit.U5, CaptureUnit.U6, CaptureUnit.U7],
    CaptureModule.U2 : [CaptureUnit.U8],
    CaptureModule.U3 : [CaptureUnit.U9]
}

def construct_capture_modules(cap_ctrl):
    for cap_mod, cap_units in CAP_MOD_TO_UNITS.items():
        cap_ctrl.construct_capture_module(cap_mod, *cap_units)


def set_trigger_awg(cap_ctrl, awg, capture_modules):
    for cap_mod_id in capture_modules:
        cap_ctrl.select_trigger_awg(cap_mod_id, awg)
        cap_ctrl.enable_start_trigger(*CAP_MOD_TO_UNITS[cap_mod_id])


def gen_cos_wave(freq, num_cycles, amp, sampling_rate, smallest_unit_of_wave_len):
    """
    freq : MHz
    """
    i_data =  SinWave(num_cycles = num_cycles, frequency = freq, amplitude = amp, phase = math.pi / 2)
    q_data =  SinWave(num_cycles = num_cycles, frequency = freq, amplitude = amp)
    return IqWave(i_data, q_data).gen_samples(sampling_rate, smallest_unit_of_wave_len)


def gen_wave_seq(sampling_rate):
    wave_seq = WaveSequence(
        num_wait_words = 16,
        num_repeats = 1,
        design_type = E7AwgHwType.SIMPLE_MULTI)

    num_chunks = 1
    samples = gen_cos_wave(
        42e6, NUM_WAVE_CYCLES, 32760, sampling_rate, wave_seq.smallest_unit_of_wave_len)
    for _ in range(num_chunks):
        wave_seq.add_chunk(
            iq_samples = samples,
            num_blank_words = 0, 
            num_repeats = NUM_CHUNK_REPEATS)
    return wave_seq
 

def set_wave_sequence(awg_ctrl):
    awg_to_wave_sequence = {}
    wave_seq = gen_wave_seq(awg_ctrl.sampling_rate())
    for awg_id in sorted(AWG.on(E7AwgHwType.SIMPLE_MULTI)):
        awg_to_wave_sequence[awg_id] = wave_seq
        awg_ctrl.set_wave_sequence(awg_id, wave_seq)
    return awg_to_wave_sequence


def set_capture_params(cap_ctrl, wave_seq, capture_units, use_integ):
    capture_param = gen_capture_param(wave_seq, use_integ)
    for captu_unit_id in capture_units:
        cap_ctrl.set_capture_params(captu_unit_id, capture_param)


def gen_capture_param(wave_seq, use_integ):
    capture_param = CaptureParam()
    capture_param.capture_delay = CAPTURE_DELAY
    capture_param.num_integ_sections = NUM_CHUNK_REPEATS - 1
    # 積算区間長を出力波形の 1 チャンク分と同じ長さになるように設定する
    capture_param.add_sum_section(wave_seq.chunk(0).num_wave_words - 1, 1)

    if use_integ:
        capture_param.sel_dsp_units_to_enable(DspUnit.INTEGRATION, DspUnit.CLASSIFICATION)
    else:
        capture_param.sel_dsp_units_to_enable(DspUnit.CLASSIFICATION)
    capture_param.set_decision_func_params(
        DecisionFunc.U0, np.float32(1), np.float32(1), np.float32(0))
    capture_param.set_decision_func_params(
        DecisionFunc.U1, np.float32(-1), np.float32(1), np.float32(0))

    return capture_param


def get_capture_data(cap_ctrl, capture_units):
    capture_unit_to_capture_data = {}
    for capture_unit_id in capture_units:
        num_captured_samples = cap_ctrl.num_captured_samples(capture_unit_id)
        capture_unit_to_capture_data[capture_unit_id] = \
            cap_ctrl.get_classification_results(capture_unit_id, num_captured_samples)
    return capture_unit_to_capture_data


def save_wave_data(prefix, sampling_rate, id_to_samples):
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


def save_classification_results(prefix, id_to_results):
    for id, results in id_to_results.items():
        dir = SAVE_DIR + '/{}_{}'.format(prefix, id)
        os.makedirs(dir, exist_ok = True)
        print('save {} {} data'.format(prefix, id))

        # 四値化結果をテキストファイルに保存
        filepath = dir + '/{}_{}.txt'.format(prefix, id)
        with open(filepath, 'w') as txt_file:
            for result in results:
                txt_file.write("{}\n".format(result))


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


def create_awg_ctrl(use_labrad, server_ip_addr):
    if use_labrad:
        return RemoteAwgCtrl(server_ip_addr, IP_ADDR, E7AwgHwType.SIMPLE_MULTI)
    else:
        return AwgCtrl(IP_ADDR, E7AwgHwType.SIMPLE_MULTI)


def create_capture_ctrl(use_labrad, server_ip_addr):
    if use_labrad:
        return RemoteCaptureCtrl(server_ip_addr, IP_ADDR, E7AwgHwType.SIMPLE_MULTI)
    else:
        return CaptureCtrl(IP_ADDR, E7AwgHwType.SIMPLE_MULTI)


def main(awgs, capture_modules, use_labrad, server_ip_addr, use_integ):
    capture_units = [CAP_MOD_TO_UNITS[cap_mod] for cap_mod in capture_modules]
    capture_units = sum(capture_units, []) # flatten
    with (create_awg_ctrl(use_labrad, server_ip_addr) as awg_ctrl,
          create_capture_ctrl(use_labrad, server_ip_addr) as cap_ctrl):
        # 初期化
        awg_ctrl.initialize(*awgs)
        cap_ctrl.initialize(*capture_units)
        # キャプチャモジュールの構成を設定
        construct_capture_modules(cap_ctrl)
        # トリガ AWG の設定
        set_trigger_awg(cap_ctrl, awgs[0], capture_modules)
        # 波形シーケンスの設定
        awg_to_wave_sequence = set_wave_sequence(awg_ctrl)
        # キャプチャパラメータの設定
        set_capture_params(cap_ctrl, awg_to_wave_sequence[awgs[0]], capture_units, use_integ)
        # 波形送信スタート
        awg_ctrl.start_awgs(*awgs)
        # 波形送信完了待ち
        awg_ctrl.wait_for_awgs_to_stop(5, *awgs)
        # キャプチャ完了待ち
        cap_ctrl.wait_for_capture_units_to_stop(600, *capture_units)
        # エラーチェック
        check_err(awg_ctrl, cap_ctrl, awgs, capture_units)
        # キャプチャデータ取得
        capture_unit_to_capture_data = get_capture_data(cap_ctrl, capture_units)

        # 波形保存
        # awg_to_wave_data = {awg: wave_seq.all_samples(False) for awg, wave_seq in awg_to_wave_sequence.items()}
        # save_wave_data('awg', awg_ctrl.sampling_rate(), awg_to_wave_data) # 時間がかかるので削除
        save_classification_results('capture', capture_unit_to_capture_data)
        print('end')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr')
    parser.add_argument('--awgs')
    parser.add_argument('--capture-module')
    parser.add_argument('--server-ipaddr')
    parser.add_argument('--labrad', action='store_true')
    parser.add_argument('--integ', action='store_true')
    args = parser.parse_args()

    if args.ipaddr is not None:
        IP_ADDR = args.ipaddr

    awgs = sorted(AWG.on(E7AwgHwType.SIMPLE_MULTI))
    if args.awgs is not None:
        awgs = [AWG.of(int(x)) for x in args.awgs.split(',')]

    capture_modules = sorted(CaptureModule.on(E7AwgHwType.SIMPLE_MULTI))
    if args.capture_module is not None:
        capture_modules = [CaptureModule.of(int(args.capture_module))]

    server_ip_addr = 'localhost'
    if args.server_ipaddr is not None:
        server_ip_addr = args.server_ipaddr

    main(awgs, capture_modules, args.labrad, server_ip_addr, args.integ)
