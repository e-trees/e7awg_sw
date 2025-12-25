"""
AWG から余弦波を出力する.
"""
import os
import math
import argparse
import e7awgsw as e7s
import e7awgsw.zcu216 as e7sz
from collections import namedtuple

IpAddr = namedtuple('IpAddr', ['zcu216', 'fpga'])

# AWG から出力する余弦波のパラメータ
NUM_FREQ = 1 # MHz
NUM_CYCLES = 4
AMPLITUDE = 28000

def gen_cos_wave(num_cycles, freq, amp, hw_specs):
    """
    freq : MHz
    """
    samples = e7s.SinWave(num_cycles, freq * 1e6, amp, phase = math.pi / 2) \
        .gen_samples(hw_specs.awg.sampling_rate)
    # 波形データに 0 データを足して, その長さを波形パートを構成可能なサンプル数の最小単位の倍数に合わせる.
    reminder = len(samples) % hw_specs.awg.smallest_unit_of_wave_len
    if reminder != 0:
        zeros = [0] * (hw_specs.awg.smallest_unit_of_wave_len - reminder)
        samples.extend(zeros)
    return samples


def gen_cos_wave_seq(num_wait_words, num_chunks, hw_specs):
    wave_seq = e7s.WaveSequence(
        num_wait_words = num_wait_words,
        num_repeats = 1,
        design_type = hw_specs.design_type)
    i_samples = gen_cos_wave(NUM_CYCLES, NUM_FREQ, AMPLITUDE, hw_specs)
    q_samples = [0] * len(i_samples)
    for _ in range(num_chunks):
        wave_seq.add_chunk(
            iq_samples = list(zip(i_samples, q_samples)),
            num_blank_words = 0,
            num_repeats = 1)
    return wave_seq


def set_wave_sequence(awg_ctrl, awgs, num_wait_words, hw_specs):
    awg_to_wave_sequence = {}
    for awg_id in awgs:
        wave_seq = gen_cos_wave_seq(num_wait_words, 1, hw_specs)
        awg_to_wave_sequence[awg_id] = wave_seq
        awg_ctrl.set_wave_sequence(awg_id, wave_seq)
    return awg_to_wave_sequence


def check_err(awg_ctrl, awgs):
    awg_to_err = awg_ctrl.check_err(*awgs)
    for awg_id, err_list in awg_to_err.items():
        print(awg_id)
        for err in err_list:
            print('    {}'.format(err))


def output_graph(awg_to_wave_seq):
    for awg_id, wave_seq in awg_to_wave_seq.items():
        dirpath = 'plot_send_wave/AWG_{}/'.format(awg_id)
        os.makedirs(dirpath, exist_ok=True)
        iq_samples = wave_seq.all_samples(True)
        i_samples = [iq_sample[0] for iq_sample in iq_samples]
        e7s.plot_samples(i_samples, 'I waveform', dirpath + "i_samples.png")
        q_samples = [iq_sample[1] for iq_sample in iq_samples]
        e7s.plot_samples(q_samples, 'Q waveform', dirpath + "q_samples.png")


def setup_dacs(rfdc_ctrl):
    """DAC の設定を行う"""
    for tile in list(e7sz.DacTile):
        # FIFO 無効化
        rfdc_ctrl.disable_dac_fifo(tile)
        for channel in list(e7sz.DacChannel):
            # ミキサの設定 
            # 周波数 = 0 [MHz], 初期位相 = 0 [degrees], 振幅 = 0.7
            rfdc_ctrl.set_dac_mixer_settings(tile, channel, 0, 0, e7sz.MixerScale.V0P7)
            # DAC 割り込みクリア
            rfdc_ctrl.clear_dac_interrupts(tile, channel, *list(e7sz.RfdcInterrupt))
            # DAC 割り込み有効化
            rfdc_ctrl.enable_dac_interrupts(tile, channel, *list(e7sz.RfdcInterrupt))
        # FIFO 有効化
        rfdc_ctrl.enable_dac_fifo(tile)
    # DAC タイルを同期させる.  ミキサの設定を行ってから実行する必要がある.
    rfdc_ctrl.sync_dac_tiles()


def get_dac_interrupts(rfdc_ctrl):
    """全ての DAC の割り込みを取得する"""
    dac_to_interrupts = {}
    for tile in list(e7sz.DacTile):
        dac_to_interrupts[tile] = {}
        for channel in list(e7sz.DacChannel):
            dac_to_interrupts[tile][channel] = rfdc_ctrl.get_dac_interrupts(tile, channel)
    
    return dac_to_interrupts


def output_rfdc_interrupt_details(dac_to_interrupts):
    """RF Data Converter の割り込みを出力する"""
    for tile, channel_to_interrupts in dac_to_interrupts.items():
        for channel, interrupts in channel_to_interrupts.items():
            if len(interrupts) != 0:
                print('Interrupts on DAC tile {}, channel {}'.format(tile, channel))
            for interrupt in interrupts:
                print('  ', e7sz.RfdcInterrupt.to_msg(interrupt))


def main(
    design_type,
    ip_addr,
    awgs,
    num_wait_words,
    forward_packet,
    timeout):
    hw_specs = e7s.E7AwgHwSpecs(design_type)
    with (e7sz.RftoolTransceiver(ip_addr.zcu216, 15) as transceiver,
          e7sz.RfdcCtrl(transceiver, design_type) as rfdc_ctrl,
          e7s.AwgCtrl(ip_addr.fpga, design_type) as awg_ctrl):
        # FPGA コンフィギュレーション
        print('configure FPGA')
        e7sz.configure_fpga(transceiver, design_type)
        # パケットフォワーディング開始
        if forward_packet:
            print('enable packet forwarding')
            e7sz.enable_packet_forwarding(transceiver, design_type)
        # DAC のセットアップ
        print('setup DACs')
        setup_dacs(rfdc_ctrl)
        # 初期化
        print('setup AWGs')
        awg_ctrl.initialize(*awgs)
        # 波形シーケンスの設定
        awg_to_wave_sequence = set_wave_sequence(awg_ctrl, awgs, num_wait_words, hw_specs)
        # 波形送信スタート
        print('start AWGs')
        awg_ctrl.start_awgs(*awgs)
        # 波形送信完了待ち
        print('wait for AWGs to stop')
        awg_ctrl.wait_for_awgs_to_stop(timeout, *awgs)
        # DAC 割り込みチェック
        print('check DAC interrupts')
        dac_to_interrupts = get_dac_interrupts(rfdc_ctrl)
        output_rfdc_interrupt_details(dac_to_interrupts)
        # エラーチェック
        print('check AWG errors')
        check_err(awg_ctrl, awgs)
        # 波形保存
        print('output AWG waveforms')
        output_graph(awg_to_wave_sequence)
        # パケットフォワーディング終了
        if forward_packet:
            print('disable packet forwarding')
            e7sz.disable_packet_forwarding(transceiver)
        print('end')


def get_program_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr', default='192.168.1.3', type=str)
    parser.add_argument('--awgs')
    parser.add_argument('--num-wait-words', default=0, type=int)
    parser.add_argument('--timeout', default=5, type=int)
    parser.add_argument('--forward-packet', action="store_true")
    return parser.parse_args()

if __name__ == "__main__":
    args = get_program_args()
    if args.forward_packet:
        ip_addr = IpAddr(args.ipaddr, args.ipaddr)
    else:
        ip_addr = IpAddr(args.ipaddr, '10.0.0.16')

    awgs = sorted(e7s.AWG.on(e7s.E7AwgHwType.ZCU216))
    if args.awgs is not None:
        awgs = [e7s.AWG(int(x)) for x in args.awgs.split(',')]

    main(
        e7s.E7AwgHwType.ZCU216, 
        ip_addr,
        awgs, 
        args.num_wait_words, 
        args.forward_packet,
        args.timeout)
