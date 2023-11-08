import os
import math
import argparse
import time
import numpy as np
from e7awgsw import CaptureUnit, CaptureModule, AWG, WaveSequence, CaptureParam, plot_graph
from e7awgsw import AwgStartCmd, CaptureEndFenceCmd, WaveSequenceSetCmd, CaptureParamSetCmd, CaptureAddrSetCmd, FeedbackCalcOnClassificationCmd
from e7awgsw import AwgStartCmdErr, CaptureEndFenceCmdErr, WaveSequenceSetCmdErr, CaptureParamSetCmdErr, CaptureAddrSetCmdErr, FeedbackCalcOnClassificationCmdErr
from e7awgsw import FeedbackChannel, CaptureParamElem, DspUnit, DecisionFunc
from e7awgsw import AwgCtrl, CaptureCtrl, SequencerCtrl
from e7awgsw import SinWave, IqWave
from e7awgsw.labrad import RemoteAwgCtrl, RemoteCaptureCtrl, RemoteSequencerCtrl

CAPTURE_DELAY = 0
SAVE_DIR = "result_seq_send_recv/"


def set_trigger_awg(cap_ctrl, awg, capture_modules):
    for cap_mod_id in capture_modules:
        cap_ctrl.select_trigger_awg(cap_mod_id, awg)
        cap_ctrl.enable_start_trigger(*CaptureModule.get_units(cap_mod_id))


def gen_cos_wave(freq, num_cycles, phase, amp):
    """
    freq : MHz
    """
    i_wave = SinWave(num_cycles, freq * 1e6, amp, phase = math.pi / 2 + phase)
    q_wave = SinWave(num_cycles, freq * 1e6, amp, phase = phase)
    iq_samples = IqWave(i_wave, q_wave).gen_samples(
            sampling_rate = AwgCtrl.SAMPLING_RATE, 
            padding_size = WaveSequence.NUM_SAMPLES_IN_WAVE_BLOCK)
    
    return iq_samples


def gen_wave_seq(freq, num_cycles, num_wait_words = 32, phase = 0):
    """
    freq : MHz
    """
    wave_seq = WaveSequence(
        num_wait_words = num_wait_words,
        num_repeats = 1)
        
    num_chunks = 1
    for _ in range(num_chunks):
        wave_seq.add_chunk(
            iq_samples = gen_cos_wave(freq, num_cycles, phase, 5000),
            num_blank_words = 0, 
            num_repeats = 1)

    return wave_seq


def register_wave_sequences(awg_ctrl, awgs, wave_sequences, registry_keys):
    for awg_id in awgs:
        key_to_wave_seq = dict(zip(registry_keys, wave_sequences))
        awg_ctrl.register_wave_sequences(awg_id, key_to_wave_seq)


def gen_capture_param(wave_seq, classify):
    capture_param = CaptureParam()
    capture_param.num_integ_sections = 1
    capture_param.add_sum_section(wave_seq.num_all_words - wave_seq.num_wait_words, 1) # 総和区間を 1 つだけ定義する
    capture_param.capture_delay = CAPTURE_DELAY
    if classify:
        coef_a = np.float32(1)
        coef_b = np.float32(1)
        capture_param.sel_dsp_units_to_enable(DspUnit.CLASSIFICATION)
        capture_param.set_decision_func_params(DecisionFunc.U0, coef_a, coef_b, np.float32(0))
        capture_param.set_decision_func_params(DecisionFunc.U1, coef_a, -coef_b, np.float32(0))
    return capture_param


def register_capture_params(cap_ctrl, capture_params, registry_keys):
    for i in range(len(registry_keys)):
        cap_ctrl.register_capture_params(registry_keys[i], capture_params[i])


def get_capture_data(cap_ctrl, capture_units, addr_offset):
    cap_unit_to_capture_data = {}
    for cap_unit_id in capture_units:
        num_captured_samples = cap_ctrl.num_captured_samples(cap_unit_id)
        cap_unit_to_capture_data[cap_unit_id] = \
            cap_ctrl.get_capture_data(cap_unit_id, num_captured_samples, addr_offset)
    return cap_unit_to_capture_data


def push_commands(seq_ctrl, awgs, capture_units, key_table, addr_offset):
    # キャプチャユニット 0 のキャプチャデータから算出されるフィードバック値を参照してパラメータを設定する
    fb_channel = FeedbackChannel.of(capture_units[0])
    # パラメータ設定にかかるサイクル数 (1 サイクル = 8[ns])
    time = 3875  # 31[us]
    cmds = [
        # 1 回目の波形出力とキャプチャの設定.
        # フィードバック値によらず, key_table[0] に登録されたパラメータをロードする
        WaveSequenceSetCmd(1, awgs, key_table[0]),
        CaptureParamSetCmd(2, capture_units, key_table[0]),
        CaptureAddrSetCmd(3, capture_units, 0),
        
        # 1 回目の波形出力 & キャプチャ完了待ち
        AwgStartCmd(4, awgs, time, wait = False),
        CaptureEndFenceCmd(5, capture_units, time + 2000, wait = True),
     
        # フィードバック値計算
        FeedbackCalcOnClassificationCmd(6, capture_units, 0),
     
        # 2 回目の波形出力とキャプチャの設定
        WaveSequenceSetCmd(6, awgs, key_table[1:], fb_channel),
        CaptureParamSetCmd(7, capture_units, key_table[1:], fb_channel),
        CaptureAddrSetCmd(8, capture_units, addr_offset),
     
        # 2 回目の波形出力 & キャプチャ完了待ち
        AwgStartCmd(9, awgs, 2 * time + 2000, wait = False),
        CaptureEndFenceCmd(
            10, capture_units, 2 * time + 4000, wait = True, stop_seq = True)
    ]
    seq_ctrl.push_commands(cmds)


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


def check_err(seq_ctrl, awg_ctrl, cap_ctrl, awgs, capture_units):
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

    for report in seq_ctrl.pop_cmd_err_reports():
        print(report, '\n')


def create_awg_ctrl(use_labrad, ip_addr, server_ip_addr):
    if use_labrad:
        return RemoteAwgCtrl(server_ip_addr, ip_addr)
    else:
        return AwgCtrl(ip_addr)


def create_capture_ctrl(use_labrad, ip_addr, server_ip_addr):
    if use_labrad:
        return RemoteCaptureCtrl(server_ip_addr, ip_addr)
    else:
        return CaptureCtrl(ip_addr)


def create_sequencer_ctrl(use_labrad, ip_addr, server_ip_addr):
    if use_labrad:
        return RemoteSequencerCtrl(server_ip_addr, ip_addr)
    else:
        return SequencerCtrl(ip_addr)


def main(
    awgs, 
    capture_modules, 
    use_labrad, 
    awg_cap_ip_addr,
    server_ip_addr,
    seq_ipaddr,
    num_wait_words, 
    save_dir=SAVE_DIR):

    with (create_awg_ctrl(use_labrad, awg_cap_ip_addr, server_ip_addr) as awg_ctrl,
          create_capture_ctrl(use_labrad, awg_cap_ip_addr, server_ip_addr) as cap_ctrl,
          create_sequencer_ctrl(use_labrad, seq_ipaddr, server_ip_addr) as seq_ctrl):
        
        # 初期化
        capture_units = CaptureModule.get_units(*capture_modules)
        awg_ctrl.initialize(*awgs)
        cap_ctrl.initialize(*capture_units)
        seq_ctrl.initialize()
        # トリガ AWG の設定
        set_trigger_awg(cap_ctrl, awgs[0], capture_modules)

        # 波形/キャプチャパラメータレジストリキー
        # [0] => 最初に行う送受信の波形/キャプチャパラメータのレジストリキー
        # [1] => フィードバック値が 0 だった場合の波形/キャプチャパラメータのレジストリキー
        # [2] => フィードバック値が 1 だった場合の波形/キャプチャパラメータのレジストリキー
        # [3] => フィードバック値が 2 だった場合の波形/キャプチャパラメータのレジストリキー
        # [4] => フィードバック値が 3 だった場合の波形/キャプチャパラメータのレジストリキー
        registry_keys = [0, 1, 2, 3, 4]

        # [0]  => 1 回目の送信の波形パラメータ
        # [1~4] => 2 回目の送信の波形パラメータ (フィードバック値によって送信される波形が異なる)
        freq_num_cycles_list = [(2, 1), (3, 2), (6, 4), (12, 6), (24, 8)] # (MHz, サイクル数)
    
        # 波形シーケンスの作成と登録
        freq, num_cycles = freq_num_cycles_list[0]
        wave_sequences = [gen_wave_seq(freq, num_cycles, num_wait_words, phase = 0)]
        wave_sequences += [
            gen_wave_seq(freq, num_cycles, num_wait_words) for freq, num_cycles in freq_num_cycles_list[1:]]
        register_wave_sequences(awg_ctrl, awgs, wave_sequences, registry_keys)
        # キャプチャパラメータの作成と登録
        capture_params = [gen_capture_param(wave_sequences[0], classify = True)]
        capture_params += [gen_capture_param(wave_seq, classify = False) for wave_seq in wave_sequences[1:]]
        register_capture_params(cap_ctrl, capture_params, registry_keys)
        # キャプチャパラメータからキャプチャアドレスオフセットを計算
        addr_offset = capture_params[0].calc_required_capture_mem_size()
        # コマンドを送信
        push_commands(seq_ctrl, awgs, capture_units, registry_keys, addr_offset)
        # コマンドエラーレポート送信の有効化
        seq_ctrl.enable_cmd_err_report()
        ## コマンドの処理をスタート
        #seq_ctrl.start_sequencer()
        print("wait for global kick")
        # コマンドの処理終了待ち
        seq_ctrl.wait_for_sequencer_to_stop(120)
        # エラー出力
        check_err(seq_ctrl, awg_ctrl, cap_ctrl, awgs, capture_units)
        # キャプチャデータ取得
        cap_unit_to_capture_data = get_capture_data(cap_ctrl, capture_units, addr_offset)
        # 波形保存
        save_wave_data('capture', CaptureCtrl.SAMPLING_RATE, cap_unit_to_capture_data, save_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr', default='10.1.0.255')
    parser.add_argument('--awgs')
    parser.add_argument('--capture-module')
    parser.add_argument('--server-ipaddr', default='localhost')
    parser.add_argument('--seq-ipaddr', default='10.2.0.255')
    parser.add_argument('--labrad', action='store_true')
    parser.add_argument('--num-wait-words', default=32, type=int)
    parser.add_argument('--save-dir', default=SAVE_DIR)
    args = parser.parse_args()

    awgs =  AWG.all()
    if args.awgs is not None:
        awgs = [AWG.of(int(x)) for x in args.awgs.split(',')]

    capture_modules = [CaptureModule.U0, CaptureModule.U1]
    if args.capture_module is not None:
        capture_modules = [CaptureModule.of(int(args.capture_module))]

    main(
        awgs,
        capture_modules,
        args.labrad,
        args.ipaddr,
        args.server_ipaddr,
        args.seq_ipaddr,
        args.num_wait_words,
        save_dir=args.save_dir)
    
