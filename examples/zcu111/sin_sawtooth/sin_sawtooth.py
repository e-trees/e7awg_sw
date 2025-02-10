"""
AWG から余弦波を出力する.
"""
import os
import math
import argparse
import e7awgsw as e7s
import e7awgsw.zcu111 as e7sz
from enum import Enum

class Waveform(Enum):
    SIN = 0
    SAWTOOTH = 1

def gen_sin_wave(num_samples, amp):
    return [int(amp * math.sin(2 * math.pi * i / num_samples)) for i in range(num_samples)]
    

def gen_sawtooth_wave(num_samples, amp):
    return [amp * i // num_samples for i in range(num_samples)]


def get_wave_seq_structure(num_cycles, num_cycles_in_chunk, max_chunk_repeats):
    """波形シーケンス内部の繰り返し構造を求める"""
    max_cycles_in_chunk_repeats = num_cycles_in_chunk * max_chunk_repeats

    # 1 チャンクが最大 33280 サンプルの場合, 波形メモリには 9 チャンク分の波形データを格納可能.
    # サイクル数が max_cycles 以下の波形は全て 9 チャンク以下で構築可能になるように max_cycles を定める.
    max_cycles = max_cycles_in_chunk_repeats * 8
    if num_cycles > max_cycles:
        raise ValueError("The maximum number of the waveform cycles is {}.  ({} was specified.)"
            .format(max_cycles, num_cycles))   

    # num_chunks_with_max_repeats != 0 の場合, 1 つのチャンクが最大回数繰り返される.
    num_chunks_with_max_repeats = num_cycles // max_cycles_in_chunk_repeats
    num_remaining_cycles = num_cycles - max_cycles_in_chunk_repeats * num_chunks_with_max_repeats
    # num_chunk_repeats != 0 の場合, 1 つのチャンクが num_chunk_repeats 回繰り返される
    num_chunk_repeats = num_remaining_cycles // num_cycles_in_chunk
    # num_fractional_cycles != 0 の場合, 1 つのチャンクが num_fractional_cycles サイクルのデータを 1 回出力する
    num_fractional_cycles = num_remaining_cycles - num_cycles_in_chunk * num_chunk_repeats

    return 1, num_chunks_with_max_repeats, num_chunk_repeats, num_fractional_cycles


def gen_wave_seq(waveform, num_wait_words, num_cycles, hw_specs):
    # DAC 内部での補間を行う前の 1 サイクルあたりのサンプル数.
    # DAC で 2 倍補間してから 6.51264 Gsps で出力すると約 50MHz の波形となる.
    num_samples_in_cycle = 65
    # 1 チャンクあたりのサンプル数   ※ smallest_unit_of_wave_len の倍数にする必要がある
    num_samples_in_chunk = math.lcm(hw_specs.awg.smallest_unit_of_wave_len, num_samples_in_cycle)
    # 1 チャンクあたりのサイクル数
    num_cycles_in_chunk = num_samples_in_chunk // num_samples_in_cycle

    if num_cycles <= 0:
        num_seq_repeats = hw_specs.awg.max_sequence_repeats
        num_chunks_with_max_repeats = 9
        num_chunk_repeats = 0
        num_fractional_cycles = 0
    else:
        num_seq_repeats, \
        num_chunks_with_max_repeats, \
        num_chunk_repeats, \
        num_fractional_cycles = \
            get_wave_seq_structure(num_cycles, num_cycles_in_chunk, hw_specs.awg.max_chunk_repeats)

    amplitude = 28000 # これ以上振幅を大きくすると, 補間処理でサンプル値がオーバーフローする
    if waveform == Waveform.SIN:
        i_samples = gen_sin_wave(num_samples_in_cycle, amplitude) * num_cycles_in_chunk
    else:
        i_samples = gen_sawtooth_wave(num_samples_in_cycle, amplitude) * num_cycles_in_chunk

    q_samples = [0] * len(i_samples)
    iq_samples = list(zip(i_samples, q_samples))

    wave_seq = e7s.WaveSequence(
        num_wait_words = num_wait_words,
        num_repeats = num_seq_repeats,
        design_type = hw_specs.design_type)

    for _ in range(num_chunks_with_max_repeats):
        wave_seq.add_chunk(
            iq_samples = iq_samples,
            num_blank_words = 0,
            num_repeats = hw_specs.awg.max_chunk_repeats)
    
    if num_chunk_repeats != 0:
        wave_seq.add_chunk(
            iq_samples = iq_samples,
            num_blank_words = 0,
            num_repeats = num_chunk_repeats)

    if num_fractional_cycles != 0:
        num_fractional_samples = num_fractional_cycles * num_samples_in_cycle
        zero_padding = [(0, 0)] * (num_samples_in_chunk - num_fractional_samples)
        iq_samples = iq_samples[0 : num_fractional_samples] + zero_padding
        wave_seq.add_chunk(
            iq_samples = iq_samples,
            num_blank_words = 0,
            num_repeats = 1)

    return wave_seq


def set_wave_sequence(awg_ctrl, awg_to_wave, num_wait_words, num_cycles, hw_specs):
    awg_to_wave_sequence = {}
    for awg, waveform in awg_to_wave.items():
        wave_seq = gen_wave_seq(waveform, num_wait_words, num_cycles, hw_specs)
        awg_to_wave_sequence[awg] = wave_seq
        awg_ctrl.set_wave_sequence(awg, wave_seq)
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
        samples = wave_seq.all_samples(True)
        e7s.plot_samples(samples, 'waveform', dirpath + "waveform.png")


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
    awg_to_wave,
    num_wait_words,
    num_cycles,
    timeout
):
    zcu111_ip_addr = '192.168.1.3'
    fpga_ip_addr = '10.0.0.16'
    hw_specs = e7s.E7AwgHwSpecs(design_type)
    awgs = awg_to_wave.keys()
    with (e7sz.RftoolTransceiver(zcu111_ip_addr, 15) as transceiver,
          e7sz.RfdcCtrl(transceiver, design_type) as rfdc_ctrl,
          e7s.AwgCtrl(fpga_ip_addr, design_type) as awg_ctrl):
        # FPGA コンフィギュレーション
        e7sz.configure_fpga(transceiver, design_type)
        # # DAC のセットアップ
        setup_dacs(rfdc_ctrl)
        # 初期化
        awg_ctrl.initialize(*awgs)
        # 波形シーケンスの設定
        awg_to_wave_sequence = set_wave_sequence(
            awg_ctrl, awg_to_wave, num_wait_words, num_cycles, hw_specs)
        # 波形送信スタート
        awg_ctrl.start_awgs(*awgs)
        # 波形送信完了待ち
        awg_ctrl.wait_for_awgs_to_stop(timeout, *awgs)
        # DAC 割り込みチェック
        dac_to_interrupts = get_dac_interrupts(rfdc_ctrl)
        output_rfdc_interrupt_details(dac_to_interrupts)
        # エラーチェック
        check_err(awg_ctrl, awgs)
        # 波形保存
        # output_graph(awg_to_wave_sequence) # 時間がかかるのでコメントアウトする
        print('end')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr')
    parser.add_argument('--sin-awgs')
    parser.add_argument('--sawtooth-awgs')
    parser.add_argument('--num-wait-words', default=0, type=int)
    parser.add_argument('--num-cycles', default=1, type=int)
    parser.add_argument('--timeout', default=math.inf, type=float)
    args = parser.parse_args()

    if args.ipaddr is not None:
        IP_ADDR = args.ipaddr

    sin_awgs = [e7s.AWG.U0]
    if args.sin_awgs is not None:
        sin_awgs = [e7s.AWG(int(x)) for x in args.sin_awgs.split(',')]

    sawtooth_awgs = [e7s.AWG.U6]
    if args.sawtooth_awgs is not None:
        sawtooth_awgs = [e7s.AWG(int(x)) for x in args.sawtooth_awgs.split(',')]
    
    awg_to_wave = { awg: Waveform.SIN for awg in sin_awgs } | \
                  { awg: Waveform.SAWTOOTH for awg in sawtooth_awgs }

    main(
        e7s.E7AwgHwType.ZCU111_DAC_6G_URAM_X2,
        awg_to_wave,
        args.num_wait_words,
        args.num_cycles,
        args.timeout)
