"""
プログラム引数で指定した AWG からガウスパルスを出力して, 信号処理モジュールを全て無効にしてキャプチャします.
"""
import os
import argparse
from e7awgsw import CaptureUnit, CaptureModule, AWG, \
    AwgCtrl, CaptureCtrl, WaveSequence, CaptureParam, plot_graph, E7AwgHwType
from e7awgsw import SquareWave, GaussianPulse, IqWave
from e7awgsw.labrad import RemoteAwgCtrl, RemoteCaptureCtrl

IP_ADDR = '10.0.0.16'
CAPTURE_DELAY = 0
SAVE_DIR = "result_gaussian_send_recv/"
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


def gen_wave_seq(sampling_rate):
    wave_seq = WaveSequence(
        num_wait_words = 16,
        num_repeats = 1,
        design_type = E7AwgHwType.SIMPLE_MULTI)
    
    num_chunks = 1
    for _ in range(num_chunks):
        i_wave = GaussianPulse(num_cycles = 1, frequency = 2e6, amplitude = 20000, duration = 6.0, variance = 0.4)
        q_wave = SquareWave(num_cycles = 1, frequency = 2e6, amplitude = 0, duty_cycle = 0.0)
        iq_samples = IqWave(i_wave, q_wave).gen_samples(
            sampling_rate = sampling_rate,
            padding_size = wave_seq.smallest_unit_of_wave_len)

        wave_seq.add_chunk(
            iq_samples = iq_samples,
            num_blank_words = 0, 
            num_repeats = 1)
    return wave_seq


def set_wave_sequence(awg_ctrl, awgs):
    awg_to_wave_sequence = {}
    wave_seq = gen_wave_seq(awg_ctrl.sampling_rate())
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


def main(awgs, capture_modules, use_labrad, server_ip_addr):
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
        awg_to_wave_sequence = set_wave_sequence(awg_ctrl, awgs)
        # キャプチャパラメータの設定
        set_capture_params(cap_ctrl, awg_to_wave_sequence[awgs[0]], capture_units)
        # 波形送信スタート
        awg_ctrl.start_awgs(*awgs)
        # 波形送信完了待ち
        awg_ctrl.wait_for_awgs_to_stop(5, *awgs)
        # キャプチャ完了待ち
        cap_ctrl.wait_for_capture_units_to_stop(5, *capture_units)
        # エラーチェック
        check_err(awg_ctrl, cap_ctrl, awgs, capture_units)
        # キャプチャデータ取得
        capture_unit_to_capture_data = get_capture_data(cap_ctrl, capture_units)
        # 波形保存
        awg_to_wave_data = {awg: wave_seq.all_samples(False) for awg, wave_seq in awg_to_wave_sequence.items()}
        save_wave_data('awg', awg_ctrl.sampling_rate(), awg_to_wave_data)
        save_wave_data('capture', cap_ctrl.sampling_rate(), capture_unit_to_capture_data)
        print('end')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr')
    parser.add_argument('--awgs')
    parser.add_argument('--capture-module')
    parser.add_argument('--server-ipaddr')
    parser.add_argument('--labrad', action='store_true')
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

    main(awgs, capture_modules, args.labrad, server_ip_addr)
