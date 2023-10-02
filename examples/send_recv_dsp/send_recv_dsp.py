"""
AWG から 4.8MHz の余弦波を出力して, 四値化以外の信号処理モジュールを全て有効にしてキャプチャします.
フィルタおよび窓関数の係数の設定方法は, gen_capture_param() を参照してください.

総和区間 = 12 キャプチャワード
総和区間数 = 1024
積算回数 = 16

"""
import os
import math
import argparse
from e7awgsw import DspUnit, CaptureModule, AWG, AwgCtrl, CaptureCtrl, WaveSequence, CaptureParam
from e7awgsw import IqWave, plot_graph, plot_samples
from e7awgsw.labrad import RemoteAwgCtrl, RemoteCaptureCtrl

SAVE_DIR = "result_send_recv_dsp/"
IP_ADDR = '10.0.0.16'
CAPTURE_DELAY = 100
NUM_WAVE_CYCLES = 512
NUM_WAVE_SEQ_REPEATS = 16

def set_trigger_awg(cap_ctrl, awg, capture_modules):
    for cap_mod_id in capture_modules:
        cap_ctrl.select_trigger_awg(cap_mod_id, awg)
        cap_ctrl.enable_start_trigger(*CaptureModule.get_units(cap_mod_id))


def gen_cos_wave(freq, num_cycles, amp):
    """
    freq : MHz
    """
    dt = 2.0 * math.pi * (freq * 1e6) / AwgCtrl.SAMPLING_RATE
    num_samples = int(num_cycles * AwgCtrl.SAMPLING_RATE / (freq * 1e6))
    i_data =  [int(amp * math.cos(i * dt)) for i in range(num_samples)]
    q_data =  [int(amp * math.sin(i * dt)) for i in range(num_samples)]
    return IqWave.convert_to_iq_format(i_data, q_data, WaveSequence.NUM_SAMPLES_IN_WAVE_BLOCK)


def gen_wave_seq():
    wave_seq = WaveSequence(
        num_wait_words = 16,
        num_repeats = NUM_WAVE_SEQ_REPEATS)

    num_chunks = 1
    samples = gen_cos_wave(5.0, NUM_WAVE_CYCLES, 32760)
    for _ in range(num_chunks):
        wave_seq.add_chunk(
            iq_samples = samples, # 10.0MHz cos x512
            num_blank_words = 0, 
            num_repeats = 1)
    return wave_seq
 

def set_wave_sequence(awg_ctrl):
    awg_to_wave_sequence = {}
    wave_seq = gen_wave_seq()
    for awg_id in AWG.all():
        awg_to_wave_sequence[awg_id] = wave_seq
        awg_ctrl.set_wave_sequence(awg_id, wave_seq)
    return awg_to_wave_sequence


def set_capture_params(cap_ctrl, wave_seq, capture_units):
    capture_param = gen_capture_param(wave_seq)
    for captu_unit_id in capture_units:
        cap_ctrl.set_capture_params(captu_unit_id, capture_param)


def gen_capture_param(wave_seq):
    capture_param = CaptureParam()
    capture_param.num_integ_sections = wave_seq.num_repeats

    wave_words = (wave_seq.num_all_words -  wave_seq.num_wait_words)
    sum_section_len = wave_words // wave_seq.num_repeats // NUM_WAVE_CYCLES  # 出力する余弦波の1周期分を総和区間とする
    for _ in range(NUM_WAVE_CYCLES):
        # 総和区間長が 6 ワード以下の場合 decimation から値が出てこなくなるので 7 ワード以上を指定する
        capture_param.add_sum_section(sum_section_len - 1, 1)
    # 総和範囲の指定
    capture_param.sum_start_word_no = 0
    capture_param.num_words_to_sum = CaptureParam.MAX_SUM_SECTION_LEN

    capture_param.sel_dsp_units_to_enable(
        DspUnit.COMPLEX_FIR,
        DspUnit.DECIMATION,
        DspUnit.REAL_FIR,
        DspUnit.COMPLEX_WINDOW,
        DspUnit.SUM,
        DspUnit.INTEGRATION)
    capture_param.complex_fir_coefs = [1 + 0j] + [0] * (CaptureParam.NUM_COMPLEX_FIR_COEFS - 1)
    capture_param.real_fir_i_coefs = [1] + [0] * (CaptureParam.NUM_REAL_FIR_COEFS - 1)
    capture_param.real_fir_q_coefs = capture_param.real_fir_i_coefs
    capture_param.complex_window_coefs = [1 + 0j] * CaptureParam.NUM_COMPLEXW_WINDOW_COEFS
    capture_param.capture_delay = CAPTURE_DELAY
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
        return RemoteAwgCtrl(server_ip_addr, IP_ADDR)
    else:
        return AwgCtrl(IP_ADDR)


def create_capture_ctrl(use_labrad, server_ip_addr):
    if use_labrad:
        return RemoteCaptureCtrl(server_ip_addr, IP_ADDR)
    else:
        return CaptureCtrl(IP_ADDR)


def main(awgs, capture_modules, use_labrad, server_ip_addr):
    with (create_awg_ctrl(use_labrad, server_ip_addr) as awg_ctrl,
        create_capture_ctrl(use_labrad, server_ip_addr) as cap_ctrl):
        capture_units = CaptureModule.get_units(*capture_modules)
        # 初期化
        awg_ctrl.initialize(*awgs)
        cap_ctrl.initialize(*capture_units)
        # トリガ AWG の設定
        set_trigger_awg(cap_ctrl, awgs[0], capture_modules)
        # 波形シーケンスの設定
        awg_to_wave_sequence = set_wave_sequence(awg_ctrl)
        # キャプチャパラメータの設定
        set_capture_params(cap_ctrl, awg_to_wave_sequence[awgs[0]], capture_units)
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
        #awg_to_wave_data = {awg: wave_seq.all_samples(False) for awg, wave_seq in awg_to_wave_sequence.items()}
        #save_wave_data('awg', AwgCtrl.SAMPLING_RATE, awg_to_wave_data) # 時間がかかるので削除
        save_sample_data('capture', capture_unit_to_capture_data)
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

    awgs = AWG.all()
    if args.awgs is not None:
        awgs = [AWG.of(int(x)) for x in args.awgs.split(',')]

    capture_modules = CaptureModule.all()
    if args.capture_module is not None:
        capture_modules = [CaptureModule.of(int(args.capture_module))]

    server_ip_addr = 'localhost'
    if args.server_ipaddr is not None:
        server_ip_addr = args.server_ipaddr

    main(awgs, capture_modules, args.labrad, server_ip_addr)
