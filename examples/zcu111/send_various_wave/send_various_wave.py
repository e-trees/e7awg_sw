import sys
import os
import math
import e7awgsw as e7s
import e7awgsw.zcu111 as e7sz
from collections import namedtuple

WAVE_FREQ_0 = 4 # MHz
WAVE_FREQ_1 = 1.08 # MHz  (波形チャンクに波形パートを追加するときに 0 パディングが必要ない周波数)

# AWG は最大 5 つまで同時に動作可能.  5 つを超えると DRAM からの波形データ読み出しが間に合わなくなる.
awg_list = [e7s.AWG.U0, e7s.AWG.U1, e7s.AWG.U2, e7s.AWG.U3]

try:
    if sys.argv[1] == "1":
        awg_list = [e7s.AWG.U4, e7s.AWG.U5, e7s.AWG.U6, e7s.AWG.U7]
except Exception:
    pass

wave_params = namedtuple(
    'wave_params',
    ('freq', 'num_wait_words', 'num_seq_repeats', 'num_chunk_repeats', 'num_blank_words', 'chunk_waves'))

mixer_settings = namedtuple(
    'mixer_settings', ('freq', 'phase_offset', 'amplitude'))

awg_to_params = {

    # const  const  const  const  const  _  const  const  const  const  const  _  (出力パターン)
    e7s.AWG.U0 : wave_params(
        freq = WAVE_FREQ_0,
        num_wait_words = 0,
        num_seq_repeats = 1,
        num_chunk_repeats = 2,
        num_blank_words = 0,
        # chunk_waves = [ (チャンク 0 波形パターン), (チャンク 1 波形パターン), ... ]
        # (チャンク N 波形パターン) = (波形タイプ, サイクル数)
        chunk_waves = [('const', 5)]),

    # const  const  const  const  const  _  const  const  const  const  const  _
    e7s.AWG.U1 : wave_params(
        freq = WAVE_FREQ_0,
        num_wait_words = 0,
        num_seq_repeats = 1,
        num_chunk_repeats = 2,
        num_blank_words = 0,
        chunk_waves = [('const', 5)]),

    # squ  squ  squ  saw  saw  saw  squ  squ  squ  saw  saw  saw
    e7s.AWG.U2 : wave_params(
        freq = WAVE_FREQ_1,
        num_wait_words = 0,
        num_seq_repeats = 2,
        num_chunk_repeats = 3,
        num_blank_words = 0,
        chunk_waves = [('squ', 1), ('saw', 1)]),

    # _  squ  squ  saw  saw  squ  squ  saw  saw  squ  squ  saw  saw
    e7s.AWG.U3 : wave_params(
        freq = WAVE_FREQ_1,
        num_wait_words = 69,
        num_seq_repeats = 3,
        num_chunk_repeats = 2,
        num_blank_words = 0,
        chunk_waves = [('squ', 1), ('saw', 1)]),

    # sin  sin  sin  sin  sin  sin  sin  sin
    e7s.AWG.U4 : wave_params(
        freq = WAVE_FREQ_0,
        num_wait_words = 0,
        num_seq_repeats = 1,
        num_chunk_repeats = 1,
        num_blank_words = 0,
        chunk_waves = [('sin', 8)]),

    # sin  sin  sin  sin  sin  sin  sin  sin
    e7s.AWG.U5 : wave_params(
        freq = WAVE_FREQ_0,
        num_wait_words = 0,
        num_seq_repeats = 1,
        num_chunk_repeats = 1,
        num_blank_words = 0,
        chunk_waves = [('sin', 8)]),

    # sin  sin  sin  sin  sin  sin  sin  sin
    e7s.AWG.U6 : wave_params(
        freq = WAVE_FREQ_0,
        num_wait_words = 0,
        num_seq_repeats = 1,
        num_chunk_repeats = 1,
        num_blank_words = 0,
        chunk_waves = [('sin', 8)]),

    # sin  sin  sin  sin  sin  sin  sin  sin
    e7s.AWG.U7 : wave_params(
        freq = WAVE_FREQ_0,
        num_wait_words = 0,
        num_seq_repeats = 1,
        num_chunk_repeats = 1,
        num_blank_words = 0,
        chunk_waves = [('sin', 8)])
}


mixer_settings = {
    e7sz.DacTile.T0 : {
        e7sz.DacChannel.C0 : mixer_settings(
            freq = 0, # MHz
            phase_offset = 0,
            amplitude = e7sz.MixerScale.V0P7),

        e7sz.DacChannel.C1 : mixer_settings(
            freq = 1,
            phase_offset = 0,
            amplitude = e7sz.MixerScale.V0P7),

        e7sz.DacChannel.C2 : mixer_settings(
            freq = 0,
            phase_offset = 0,
            amplitude = e7sz.MixerScale.V0P7),

        e7sz.DacChannel.C3 : mixer_settings(
            freq = 0,
            phase_offset = 0,
            amplitude = e7sz.MixerScale.V0P7),
    },

    e7sz.DacTile.T1 : {
        e7sz.DacChannel.C0 : mixer_settings(
            freq = 0,
            phase_offset = 0,
            amplitude = e7sz.MixerScale.V0P7),

        e7sz.DacChannel.C1 : mixer_settings(
            freq = 1,
            phase_offset = 0,
            amplitude = e7sz.MixerScale.V0P7),

        e7sz.DacChannel.C2 : mixer_settings(
            freq = 0,
            phase_offset = 0,
            amplitude = e7sz.MixerScale.V0P7),

        e7sz.DacChannel.C3 : mixer_settings(
            freq = 1,
            phase_offset = 0,
            amplitude = e7sz.MixerScale.V0P7),
    }
}


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


def output_awg_err_details(awg_to_errs):
    """AWG のエラーを出力する"""
    for awg, errs in awg_to_errs.items():
        print('Errors on AWG {}'.format(awg))
        for err in errs:
            print('  ', e7s.AwgErr.to_msg(err))
        print()


def gen_wave_samples(waveform, freq, num_cycles, sampling_rate, hw_specs):
    """引数に応じて「正弦波」「ノコギリ波」「矩形波」のいずれかを作る"""
    if waveform == 'sin':
        wave = e7s.SinWave(num_cycles, freq, 25000)
    elif waveform == 'saw':
        wave = e7s.SawtoothWave(
            num_cycles, freq, 25000, phase = math.pi, crest_pos = 0.0)
    elif waveform == 'squ':
        wave = e7s.SquareWave(num_cycles, freq, 25000)
    elif waveform == 'const':
        wave = e7s.SquareWave(num_cycles, freq, 25000, duty_cycle = 1)

    # DAC の I/Q ミキサが有効な場合, RF Data Converter 内部で波形データが補間されるので, あらかじめ 1/2 に間引いておく.
    samples = wave.gen_samples(sampling_rate)[0::2]
    return e7s.IqWave.convert_to_iq_format(
        samples, samples, hw_specs.awg.smallest_unit_of_wave_len)


def set_waves(awg_ctrl, sampling_rate, hw_specs):
    awg_to_wave_seq = {}
    for awg_id, params in awg_to_params.items():
        wave_seq = e7s.WaveSequence(
            params.num_wait_words, params.num_seq_repeats, e7s.E7AwgHwType.ZCU111)
        for waveform, num_cycles in params.chunk_waves:
            wave_seq.add_chunk(
                gen_wave_samples(waveform, params.freq * 1e6, num_cycles, sampling_rate, hw_specs),
                params.num_blank_words,
                params.num_chunk_repeats)
            
        awg_ctrl.set_wave_sequence(awg_id, wave_seq)
        awg_to_wave_seq[awg_id] = wave_seq

    return awg_to_wave_seq


def setup_awgs(awg_ctrl, sampling_rate, hw_specs):
    """AWG の波形出力に必要な設定を行う"""
    # AWG 初期化
    awg_ctrl.initialize(*awg_list)
    # 波形データを AWG に設定
    return set_waves(awg_ctrl, sampling_rate, hw_specs)


def setup_dacs(rfdc_ctrl):
    """DAC の設定を行う"""
    for tile in mixer_settings.keys():
        # FIFO 無効化
        rfdc_ctrl.disable_dac_fifo(tile)
        for channel, setting in mixer_settings[tile].items():
            # ミキサを設定
            rfdc_ctrl.set_dac_mixer_settings(
                tile, channel, setting.freq, setting.phase_offset, setting.amplitude)
            # DAC 割り込みクリア
            rfdc_ctrl.clear_dac_interrupts(tile, channel, *list(e7sz.RfdcInterrupt))
            # DAC 割り込み有効化
            rfdc_ctrl.enable_dac_interrupts(tile, channel, *list(e7sz.RfdcInterrupt))
        # FIFO 有効化
        rfdc_ctrl.enable_dac_fifo(tile)
    
    # DAC タイルを同期させる.  ミキサの設定を行ってから実行する必要がある.
    rfdc_ctrl.sync_dac_tiles()


def set_digital_out_data(digital_out_ctrl):
    # ディジタル出力データの作成
    dout_data_list = e7s.DigitalOutputDataList(e7s.E7AwgHwType.ZCU111)
    (dout_data_list
        .add(0x01, 69)
        .add(0x02, 69)
        .add(0x04, 69)
        .add(0x08, 69)
        .add(0x10, 69)
        .add(0x20, 69)
        .add(0x40, 69)
        .add(0x80, 69))
    # 出力データをディジタル出力モジュールに設定
    digital_out_ctrl.set_output_data(dout_data_list, e7s.DigitalOut.U0)


def setup_digital_output_modules(digital_out_ctrl):
    """ディジタル出力に必要な設定を行う"""
    # ディジタル出力モジュール初期化
    digital_out_ctrl.initialize(e7s.DigitalOut.U0)
    # デフォルトのディジタル出力データの設定
    digital_out_ctrl.set_default_output_data(0x36, e7s.DigitalOut.U0)
    # ディジタル出力データの設定
    set_digital_out_data(digital_out_ctrl)
    # AWG からのスタートトリガを受け付けるように設定.
    # このスタートトリガは, いずれかの AWG の波形出力開始と同時にアサートされる.
    # なお, AwgCtrl.awgstart_awgs で複数の AWG をスタートしてもスタートトリガは一度しかアサートされない.
    digital_out_ctrl.enable_trigger(e7s.DigitalOutTrigger.START, e7s.DigitalOut.U0)


def output_graph(awg_to_wave_seq):
    for awg_id, wave_seq in awg_to_wave_seq.items():
        dirpath = 'plot_send_wave/AWG_{}/'.format(awg_id)
        os.makedirs(dirpath, exist_ok=True)
        iq_samples = wave_seq.all_samples(True)
        i_samples = [iq_sample[0] for iq_sample in iq_samples]
        e7s.plot_samples(i_samples, 'I waveform', dirpath + "i_samples.png")
        q_samples = [iq_sample[1] for iq_sample in iq_samples]
        e7s.plot_samples(q_samples, 'Q waveform', dirpath + "q_samples.png")

def main():
    zcu111_ip_addr = '192.168.1.3'
    fpga_ip_addr = '10.0.0.16'
    hw_specs = e7s.E7AwgHwSpecs(e7s.E7AwgHwType.ZCU111)
    with (e7sz.RftoolTransceiver(zcu111_ip_addr, 15) as trasnceiver,
          e7sz.RfdcCtrl(trasnceiver, e7s.E7AwgHwType.ZCU111) as rfdc_ctrl,
          e7s.AwgCtrl(fpga_ip_addr, e7s.E7AwgHwType.ZCU111) as awg_ctrl,
          e7s.DigitalOutCtrl(fpga_ip_addr, e7s.E7AwgHwType.ZCU111) as digital_out_ctrl):
        # FPGA コンフィギュレーション
        print('configure fpga')
        e7sz.configure_fpga(trasnceiver, e7s.E7AwgHwType.ZCU111)
        # DAC のセットアップ
        print('setup DACs')
        setup_dacs(rfdc_ctrl)
        # AWG のセットアップ
        print('setup AWGs')
        sampling_rate = rfdc_ctrl.get_dac_sampling_rate(e7sz.DacTile.T0) * 1e6 # Hz
        awg_to_wave_seq = setup_awgs(awg_ctrl, sampling_rate, hw_specs)
        # ディジタル出力モジュールのセットアップ
        print('setup digital output modules')
        setup_digital_output_modules(digital_out_ctrl)
        # 波形出力スタート
        print('start AWGs')
        awg_ctrl.start_awgs(*awg_list)
        # 波形出力完了待ち
        print('wait for AWGs to stop')
        awg_ctrl.wait_for_awgs_to_stop(5, *awg_list)
        # ディジタル出力モジュール動作完了待ち
        print('wait for a digital output module to stop')
        digital_out_ctrl.wait_for_douts_to_stop(5, e7s.DigitalOut.U0)
        # 波形出力完了フラグクリア
        awg_ctrl.clear_awg_stop_flags(*awg_list)
        # ディジタル出力モジュール動作完了フラグクリア
        digital_out_ctrl.clear_dout_stop_flags(e7s.DigitalOut.U0)
        # DAC 割り込みチェック
        print('check DAC interrupts')
        dac_to_interrupts = get_dac_interrupts(rfdc_ctrl)
        output_rfdc_interrupt_details(dac_to_interrupts)
        # AWG エラーチェック
        print('check AWG errors')
        awg_to_errs = awg_ctrl.check_err(*awg_list)
        output_awg_err_details(awg_to_errs)
        # グラフ出力
        print('output waveform graphs')
        output_graph(awg_to_wave_seq)


if __name__ == "__main__":
    main()
