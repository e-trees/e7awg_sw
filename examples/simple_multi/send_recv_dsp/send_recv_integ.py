"""
AWG から control 波形と readout 波形を出力して, 積算処理モジュールを有効にしてキャプチャします.
"""
import os
import math
import argparse
from collections import namedtuple
from e7awgsw import DspUnit, CaptureUnit, CaptureModule, AWG, \
    AwgCtrl, CaptureCtrl, WaveSequence, CaptureParam, E7AwgHwType
from e7awgsw import SinWave, IqWave, plot_graph, plot_samples
from e7awgsw.labrad import RemoteAwgCtrl, RemoteCaptureCtrl

SAVE_DIR = "result_send_recv_integ/"
IP_ADDR = '10.0.0.16'
ADDITIONAL_CAPTURE_DELAY = 0 # cpature words = cycyles@125MHz 
CAP_MOD_TO_UNITS = {
    CaptureModule.U0 : [CaptureUnit.U0, CaptureUnit.U1, CaptureUnit.U2, CaptureUnit.U3],
    CaptureModule.U1 : [CaptureUnit.U4, CaptureUnit.U5, CaptureUnit.U6, CaptureUnit.U7],
    CaptureModule.U2 : [CaptureUnit.U8],
    CaptureModule.U3 : [CaptureUnit.U9]
}

wave_params = namedtuple(
    'WaveParams',
    ('num_wait_words',
     'ctrl_freq',
     'ctrl_wave_len',
     'readout_freq',
     'readout_wave_len',
     'readout_blank_len',
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

def construct_capture_modules(cap_ctrl):
    for cap_mod, cap_units in CAP_MOD_TO_UNITS.items():
        cap_ctrl.construct_capture_module(cap_mod, *cap_units)


def set_trigger_awg(cap_ctrl, awg, capture_modules):
    for cap_mod_id in capture_modules:
        cap_ctrl.select_trigger_awg(cap_mod_id, awg)
        cap_ctrl.enable_start_trigger(*CAP_MOD_TO_UNITS[cap_mod_id])


def gen_cos_wave(freq, num_cycles, amp, sampling_rate):
    """
    freq : MHz
    """
    freq = freq * 1e6
    i_samples = SinWave(num_cycles = num_cycles, frequency = freq, amplitude = amp, phase = math.pi / 2).gen_samples(sampling_rate)
    q_samples = SinWave(num_cycles = num_cycles, frequency = freq, amplitude = amp).gen_samples(sampling_rate)
    return (i_samples, q_samples)


def gen_ctrl_wave_samples(params, sampling_rate):
    """
    control 波形サンプル作成
    """
    num_cycles = params.ctrl_freq * params.ctrl_wave_len * 1e-3
    return gen_cos_wave(params.ctrl_freq, num_cycles, 32760, sampling_rate)


def gen_readout_wave_samples(params, num_pre_blank_samples, sampling_rate):
    """
    readout 波形サンプル作成
    """
    num_cycles = params.readout_freq * params.readout_wave_len * 1e-3
    i_samples, q_samples = gen_cos_wave(params.readout_freq, num_cycles, 32760, sampling_rate)
    i_samples = [0] * num_pre_blank_samples + i_samples
    q_samples = [0] * num_pre_blank_samples + q_samples
    return (i_samples, q_samples)


def gen_ctrl_wave_seq(params, num_all_samples, i_samples, q_samples):
    """
    control 波形シーケンス作成
    """
    wave_seq = WaveSequence(
        num_wait_words = params.num_wait_words,
        num_repeats = 1,
        design_type = E7AwgHwType.SIMPLE_MULTI)
    iq_samples = IqWave.convert_to_iq_format(i_samples, q_samples, wave_seq.smallest_unit_of_wave_len)
    num_blank_samples = num_all_samples - len(iq_samples)
    num_blank_words = num_blank_samples // wave_seq.num_samples_in_awg_word
    wave_seq.add_chunk(
        iq_samples = iq_samples,
        num_blank_words = num_blank_words, 
        num_repeats = params.num_chunk_repeats)

    return wave_seq


def gen_readout_wave_seq(params, i_samples, q_samples, sampling_rate):
    """
    readout 波形シーケンス作成
    """
    wave_seq = WaveSequence(
        num_wait_words = params.num_wait_words,
        num_repeats = 1,
        design_type = E7AwgHwType.SIMPLE_MULTI)
    iq_samples = IqWave.convert_to_iq_format(i_samples, q_samples, wave_seq.smallest_unit_of_wave_len)
    # I/Q サンプルに付加された 0 データの分 readout 波形のブランクを短くする
    num_added_samples = len(iq_samples) - len(i_samples)
    num_blank_samples = max(
        int(sampling_rate * params.readout_blank_len / 1e3) - num_added_samples, 0)
    num_blank_words = num_blank_samples // wave_seq.num_samples_in_awg_word
    wave_seq.add_chunk(
        iq_samples = iq_samples,
        num_blank_words = num_blank_words, 
        num_repeats = params.num_chunk_repeats)

    return wave_seq


def set_wave_sequence(awg_ctrl, params):
    # サンプル作成
    ctrl_i_samples, ctrl_q_samples = gen_ctrl_wave_samples(params, awg_ctrl.sampling_rate())
    ro_i_samples, ro_q_samples = \
        gen_readout_wave_samples(params, len(ctrl_i_samples), awg_ctrl.sampling_rate())

    # 波形シーケンス作成
    ro_wave_seq = \
        gen_readout_wave_seq(params, ro_i_samples, ro_q_samples, awg_ctrl.sampling_rate())
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


def set_capture_params(cap_ctrl, ctrl_wave_seq, ro_wave_seq, capture_units):
    capture_param = gen_capture_param(ctrl_wave_seq, ro_wave_seq, cap_ctrl.sampling_rate())
    for captu_unit_id in capture_units:
        cap_ctrl.set_capture_params(captu_unit_id, capture_param)


def gen_capture_param(ctrl_wave_seq, ro_wave_seq, sampling_rate):
    capture_param = CaptureParam()
    capture_param.num_integ_sections = ro_wave_seq.chunk(0).num_repeats # 積算区間数

    # readout 波形の長さから, 追加で 1us キャプチャするためのキャプチャワード数を計算
    additional_capture_words = int(1e-6 * sampling_rate) // CaptureParam.NUM_SAMPLES_IN_ADC_WORD
    additional_capture_words = min(additional_capture_words, ro_wave_seq.chunk(0).num_blank_words - 1)

    sum_section_len = ro_wave_seq.chunk(0).num_words - ro_wave_seq.chunk(0).num_blank_words + additional_capture_words
    num_blank_words = ro_wave_seq.chunk(0).num_words - sum_section_len
    capture_param.add_sum_section(sum_section_len, num_blank_words)
    capture_param.sum_start_word_no = 0
    capture_param.num_words_to_sum = CaptureParam.MAX_SUM_SECTION_LEN
    capture_param.sel_dsp_units_to_enable(DspUnit.INTEGRATION)
    capture_param.capture_delay = ctrl_wave_seq.num_wait_words + ctrl_wave_seq.chunk(0).num_wave_words
    capture_param.capture_delay += ADDITIONAL_CAPTURE_DELAY
    # readout 波形のサンプル数とキャプチャするサンプル数が一致することを確認
    assert ro_wave_seq.num_all_samples == capture_param.num_samples_to_process
    return capture_param


def get_capture_data(cap_ctrl, capture_units):
    capture_unit_to_capture_data = {}
    for capture_unit_id in capture_units:
        num_captured_samples = cap_ctrl.num_captured_samples(capture_unit_id)
        capture_unit_to_capture_data[capture_unit_id] = cap_ctrl.get_capture_data(capture_unit_id, num_captured_samples)
    return capture_unit_to_capture_data


def save_as_text(dir, prefix, id, samples):
    filepath = dir + '/{}_{}.txt'.format(prefix, id)
    with open(filepath, 'w') as txt_file:
        for i_data, q_data in samples:
            txt_file.write("{}  ,  {}\n".format(i_data, q_data))


def save_wave_data(prefix, sampling_rate, id_to_samples):
    for id, samples in id_to_samples.items():
        print('save {} {} data'.format(prefix, id))
        dir = SAVE_DIR + '/{}_{}'.format(prefix, id)
        os.makedirs(dir, exist_ok = True)

        # I/Q データテキストファイル保存
        save_as_text(dir, prefix, id, samples)

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


def save_sample_data(prefix, id_to_samples):
    for id, samples in id_to_samples.items():
        print('save {} {} data'.format(prefix, id))
        dir = SAVE_DIR + '/{}_{}'.format(prefix, id)
        os.makedirs(dir, exist_ok = True)

        # I/Q データテキストファイル保存
        save_as_text(dir, prefix, id, samples)

        # I データグラフ保存
        i_data = [sample[0] for sample in samples]
        plot_samples(
            i_data, 
            '{}_{}_I'.format(prefix, id), 
            dir + '/{}_{}_I.png'.format(prefix, id),
            '#b44c97')

        # Q データグラフ保存
        q_data = [sample[1] for sample in samples]
        plot_samples(
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


def main(wave_params, capture_modules, use_labrad, server_ip_addr):
    capture_units = [CAP_MOD_TO_UNITS[cap_mod] for cap_mod in capture_modules]
    capture_units = sum(capture_units, []) # flatten
    with (create_awg_ctrl(use_labrad, server_ip_addr) as awg_ctrl,
          create_capture_ctrl(use_labrad, server_ip_addr) as cap_ctrl):
        # 初期化
        awg_ctrl.initialize(*AWG_LIST)
        cap_ctrl.initialize(*capture_units)
        # キャプチャモジュールの構成を設定
        construct_capture_modules(cap_ctrl)
        # トリガ AWG の設定
        set_trigger_awg(cap_ctrl, AWG_LIST.ctrl_awg_0, capture_modules)
        # 波形シーケンスの設定
        awg_to_wave_sequence = set_wave_sequence(awg_ctrl, wave_params)
        # キャプチャパラメータの設定
        set_capture_params(
            cap_ctrl,
            awg_to_wave_sequence[AWG_LIST.ctrl_awg_0],
            awg_to_wave_sequence[AWG_LIST.readout_awg_0],
            capture_units)
        # 波形送信スタート
        awg_ctrl.start_awgs(*AWG_LIST)
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
        # save_wave_data('awg', awg_ctrl.sampling_rate(), awg_to_wave_data) # 時間がかかるので削除
        save_sample_data('capture', capture_unit_to_capture_data)
        print('end')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--wavelen')
    parser.add_argument('--ipaddr')
    parser.add_argument('--capture-module')
    parser.add_argument('--server-ipaddr')
    parser.add_argument('--labrad', action='store_true')
    args = parser.parse_args()

    ctrl_wave_len = 100
    if args.wavelen is not None:
        ctrl_wave_len = int(args.wavelen)

    if args.ipaddr is not None:
        IP_ADDR = args.ipaddr

    capture_modules = sorted(CaptureModule.on(E7AwgHwType.SIMPLE_MULTI))
    if args.capture_module is not None:
        capture_modules = [CaptureModule.of(int(args.capture_module))]

    server_ip_addr = 'localhost'
    if args.server_ipaddr is not None:
        server_ip_addr = args.server_ipaddr

    wparams = wave_params(
        num_wait_words = 0,
        ctrl_freq = 100, # MHz
        ctrl_wave_len = ctrl_wave_len, # ns
        readout_freq = 100, # MHz,
        readout_wave_len = 2000, # ns,
        readout_blank_len = 0.1, # ms
        num_chunk_repeats = 10000, # 積算回数
    )

    main(wparams, capture_modules, args.labrad, server_ip_addr)
