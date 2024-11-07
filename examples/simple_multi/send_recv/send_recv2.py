"""
AWG から 50MHz の余弦波を出力して, 信号処理モジュールを全て無効にしてキャプチャします.
"""
import os
import math
import argparse
import datetime
from e7awgsw import CaptureUnit, CaptureModule, AWG, \
    AwgCtrl, CaptureCtrl, WaveSequence, CaptureParam, plot_graph, E7AwgHwType
from e7awgsw.labrad import RemoteAwgCtrl, RemoteCaptureCtrl

IP_ADDR = '10.0.0.16'
CAPTURE_DELAY = 0
SAVE_DIR = "result_send_recv/"
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


def gen_cos_wave(freq, num_cycles, amp, sampling_rate):
    """
    freq : MHz
    """
    dt = 2.0 * math.pi * (freq * 1e6) / sampling_rate
    num_samples = int(num_cycles * sampling_rate / (freq * 1e6))
    i_data = [int(amp * math.cos(i * dt)) for i in range(num_samples)]
    q_data = [int(amp * math.sin(i * dt)) for i in range(num_samples)]
    return list(zip(i_data, q_data))


def gen_wave_seq(num_wait_words, sampling_rate):
    wave_seq = WaveSequence(
        num_wait_words = num_wait_words,
        num_repeats = 1,
        design_type = E7AwgHwType.SIMPLE_MULTI)
    
    num_chunks = 1
    for i in range(num_chunks):
        samples = gen_cos_wave(2.5, 8, 5000, sampling_rate)
        # 1 波形チャンクのサンプル数は 64 の倍数でなければならない
        num_samples_in_wblcok = wave_seq.smallest_unit_of_wave_len
        if len(samples) % num_samples_in_wblcok != 0:
            additional_samples = num_samples_in_wblcok - (len(samples) % num_samples_in_wblcok)
            samples.extend([(0, 0)] * additional_samples)
        wave_seq.add_chunk(
            iq_samples = samples, # 50MHz cos x2
            num_blank_words = 0, 
            num_repeats = 3)
    return wave_seq


def set_wave_sequence(awg_ctrl, awgs, num_wait_words=16):
    awg_to_wave_sequence = {}
    wave_seq = gen_wave_seq(num_wait_words, awg_ctrl.sampling_rate())
    for awg_id in awgs:
        awg_to_wave_sequence[awg_id] = wave_seq
        awg_ctrl.set_wave_sequence(awg_id, wave_seq)
    return awg_to_wave_sequence


def set_capture_params(cap_ctrl, wave_seq, capture_units):
    capture_param = gen_capture_param(wave_seq)
    for captu_unit_id in capture_units:
        cap_ctrl.set_capture_params(captu_unit_id, capture_param)


def gen_capture_param(wave_seq):
    capture_param = CaptureParam()
    capture_param.num_integ_sections = 1
    capture_param.add_sum_section(wave_seq.num_all_words - wave_seq.num_wait_words, 1) # 総和区間を 1 つだけ定義する
    capture_param.capture_delay = CAPTURE_DELAY
    return capture_param


def get_capture_data(cap_ctrl, capture_units):
    capture_unit_to_capture_data = {}
    for capture_unit_id in capture_units:
        num_captured_samples = cap_ctrl.num_captured_samples(capture_unit_id)
        capture_unit_to_capture_data[capture_unit_id] = cap_ctrl.get_capture_data(capture_unit_id, num_captured_samples)
    return capture_unit_to_capture_data


def save_wave_data(prefix, sampling_rate, id_to_samples, save_dir=SAVE_DIR):
    for id, samples in id_to_samples.items():
        dir = save_dir + '/{}_{}'.format(prefix, id)
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


def main(
    awgs,
    capture_modules,
    use_labrad,
    server_ip_addr,
    num_wait_words,
    save_dir = SAVE_DIR,
    timeout = 5,
    use_sequencer = False):
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
        awg_to_wave_sequence = set_wave_sequence(awg_ctrl, awgs, num_wait_words)
        # キャプチャパラメータの設定
        set_capture_params(cap_ctrl, awg_to_wave_sequence[awgs[0]], capture_units)

        awg_ctrl.clear_awg_stop_flags(*awgs)
        print("wait:", datetime.datetime.now())
        if use_sequencer == False:
            # 波形送信スタート
            awg_ctrl.start_awgs(*awgs)
        else:
            print("wait for started by sequencer")
        # 波形送信完了待ち
        awg_ctrl.wait_for_awgs_to_stop(timeout, *awgs)
        print("awg done:", datetime.datetime.now())
        # キャプチャ完了待ち
        cap_ctrl.wait_for_capture_units_to_stop(timeout, *capture_units)
        # エラーチェック
        check_err(awg_ctrl, cap_ctrl, awgs, capture_units)
        # キャプチャデータ取得
        capture_unit_to_capture_data = get_capture_data(cap_ctrl, capture_units)
        # 波形保存
        awg_to_wave_data = {awg: wave_seq.all_samples(False) for awg, wave_seq in awg_to_wave_sequence.items()}
        save_wave_data('awg', awg_ctrl.sampling_rate(), awg_to_wave_data, save_dir)
        save_wave_data('capture', cap_ctrl.sampling_rate(), capture_unit_to_capture_data, save_dir)
        print('end')

        awg_ctrl.clear_awg_stop_flags(*awgs)
        print("wait:", datetime.datetime.now())
        if use_sequencer == False:
            # 波形送信スタート
            awg_ctrl.start_awgs(*awgs)
        else:
            print("wait for started by sequencer")
        # 波形送信完了待ち
        awg_ctrl.wait_for_awgs_to_stop(timeout, *awgs)
        print("awg done:", datetime.datetime.now())
        # キャプチャ完了待ち
        cap_ctrl.wait_for_capture_units_to_stop(timeout, *capture_units)
        # エラーチェック
        check_err(awg_ctrl, cap_ctrl, awgs, capture_units)
        # キャプチャデータ取得
        capture_unit_to_capture_data = get_capture_data(cap_ctrl, capture_units)
        # 波形保存
        awg_to_wave_data = {awg: wave_seq.all_samples(False) for awg, wave_seq in awg_to_wave_sequence.items()}
        save_wave_data('awg', awg_ctrl.sampling_rate(), awg_to_wave_data, save_dir)
        save_wave_data('capture', cap_ctrl.sampling_rate(), capture_unit_to_capture_data, save_dir)
        print('end')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr')
    parser.add_argument('--awgs')
    parser.add_argument('--capture-module')
    parser.add_argument('--server-ipaddr', default='localhost')
    parser.add_argument('--labrad', action='store_true')
    parser.add_argument('--num-wait-words', default=16, type=int)
    parser.add_argument('--use-sequencer', action='store_true')
    parser.add_argument('--timeout', default=5, type=int)
    parser.add_argument('--save-dir', default=SAVE_DIR)
    args = parser.parse_args()

    if args.ipaddr is not None:
        IP_ADDR = args.ipaddr

    awgs = sorted(AWG.on(E7AwgHwType.SIMPLE_MULTI))
    if args.awgs is not None:
        awgs = [AWG(int(x)) for x in args.awgs.split(',')]

    capture_modules = sorted(CaptureModule.on(E7AwgHwType.SIMPLE_MULTI))
    if args.capture_module is not None:
        capture_modules = [CaptureModule(int(args.capture_module))]

    main(
        awgs,
        capture_modules,
        args.labrad,
        args.server_ipaddr,
        args.num_wait_words,
        save_dir = args.save_dir,
        timeout = args.timeout,
        use_sequencer = args.use_sequencer)
