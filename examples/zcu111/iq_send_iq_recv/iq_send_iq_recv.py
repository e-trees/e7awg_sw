"""
AWG から余弦波を出力する.
"""
import os
import math
import argparse
import numpy as np
import e7awgsw as e7s
import e7awgsw.zcu111 as e7sz
import e7awgsw.basiccapture as bc
import sys
from collections import namedtuple

cur_dir = os.path.dirname(__file__)
sys.path.append(cur_dir + '/../calibrate_adc')
from calibrate_adc import output_calibration_wave

IpAddr = namedtuple('IpAddr', ['zcu111', 'fpga'])
WaveChunk = namedtuple('WaveChunk', ['frequency', 'num_cycles', 'amplitude', 'post_blank'])
IqSpectrum = namedtuple('IqSpectrum', ['i', 'q'])

def gen_sin_wave(num_cycles, freq, amp, phase, hw_specs):
    """
    freq : Hz
    """
    samples = e7s.SinWave(num_cycles, freq, amp, phase = phase).gen_samples(hw_specs.awg.sampling_rate)
    # 波形データに 0 データを足して, その長さを波形パートを構成可能なサンプル数の最小単位の倍数に合わせる.
    reminder = len(samples) % hw_specs.awg.smallest_unit_of_wave_len
    if reminder != 0:
        zeros = [0] * (hw_specs.awg.smallest_unit_of_wave_len - reminder)
        samples.extend(zeros)
    return samples


def add_wave_chunk(wave_seq, wave_chunk, hw_specs):
    i_samples = gen_sin_wave(
        wave_chunk.num_cycles, wave_chunk.frequency, wave_chunk.amplitude, math.pi / 2, hw_specs)
    q_samples = gen_sin_wave(
        wave_chunk.num_cycles, wave_chunk.frequency, wave_chunk.amplitude, 0, hw_specs)    
    wave_seq.add_chunk(
        iq_samples = list(zip(i_samples, q_samples)),
        num_blank_words = wave_chunk.post_blank,
        num_repeats = 1)
    return wave_seq


def set_wave_sequence(awg_ctrl, awg_to_wave_chunks, num_wait_words, hw_specs):
    awg_to_wave_sequence = {}
    for awg, wave_chunks in awg_to_wave_chunks.items():
        wave_seq = e7s.WaveSequence(
            num_wait_words = num_wait_words,
            num_repeats = 1,
            design_type = hw_specs.design_type)
        for wave_chunk in wave_chunks:
            add_wave_chunk(wave_seq, wave_chunk, hw_specs)
        awg_to_wave_sequence[awg] = wave_seq
        awg_ctrl.set_wave_sequence(awg, wave_seq)
    return awg_to_wave_sequence


def setup_awgs(awg_ctrl, awg_to_wave_chunks, num_wait_words, hw_specs):
    awg_ctrl.initialize(*list(awg_to_wave_chunks.keys()))
    return set_wave_sequence(awg_ctrl, awg_to_wave_chunks, num_wait_words, hw_specs)


def set_capture_params(cap_ctrl, cap_unit, wave_sequence, capture_delay):
    cap_param = bc.CaptureParam()
    cap_param.capture_delay = capture_delay
    cap_param.capture_data_type = e7s.SampleDataType.IQ
    for wave_chunk in wave_sequence.chunk_list:
        # キャプチャステップのキャプチャターゲットの長さを波形チャンクの波形パートと同じ長さにする.
        # キャプチャステップのポストブランクの長さを波形チャンクのポストブランクと同じ長さにする.
        # これにより, 波形チャンクの波形パートだけがキャプチャされる.
        cap_param.add_capture_step(wave_chunk.num_wave_words, wave_chunk.num_blank_words)
    cap_ctrl.set_capture_params(cap_unit, cap_param)
    return cap_param


def setup_capture_units(cap_ctrl, cap_unit_to_awg, awg_to_wave_sequence, capture_delay, hw_specs):
    cap_ctrl.initialize(*list(cap_unit_to_awg.keys()))
    cap_unit_to_cap_params = {}
    for cap_unit, awg in cap_unit_to_awg.items():
        cap_unit_specs = hw_specs.cap_units[cap_unit]
        cap_sampling_rate = cap_unit_specs.sampling_rate
        num_samples_in_cap_word = cap_unit_specs.num_samples_in_capture_word
        delay_words = int(capture_delay * cap_sampling_rate / num_samples_in_cap_word)
        wave_sequence = awg_to_wave_sequence[awg]
        cap_param = set_capture_params(cap_ctrl, cap_unit, wave_sequence, delay_words)
        cap_unit_to_cap_params[cap_unit] = cap_param
        cap_ctrl.set_trigger_awgs(cap_unit, awg)

    return cap_unit_to_cap_params


def check_awg_err(awg_ctrl, awgs):
    awg_to_err = awg_ctrl.check_err(*awgs)
    for awg, err_list in awg_to_err.items():
        print(awg)
        for err in err_list:
            print('    {}'.format(err))


def check_capture_unit_err(cap_ctrl, cap_units):
    cap_unit_to_err = cap_ctrl.check_err(*cap_units)
    for cap_unit, err_list in cap_unit_to_err.items():
        print(cap_unit)
        for err in err_list:
            print('    {}'.format(err))


def output_waveform(awg_to_wave_seq, sampling_rate, num_output_samples):
    for awg, wave_seq in awg_to_wave_seq.items():
        dirpath = 'plot_send_wave/AWG_{}/'.format(awg)
        os.makedirs(dirpath, exist_ok=True)
        samples = wave_seq.all_samples(True)[0 : num_output_samples]
        i_data = [sample[0] for sample in samples]
        q_data = [sample[1] for sample in samples]
        e7s.plot_graph(sampling_rate, [i_data, q_data], 'waveform head', dirpath + "waveform.png")


def output_capture_data(cap_unit_to_cap_data, sampling_rate, num_output_samples):
    for cap_unit, cap_data in cap_unit_to_cap_data.items():
        dirpath = 'plot_capture_data/Capture_{}/'.format(cap_unit)
        os.makedirs(dirpath, exist_ok=True)
        i_data = [sample[0] for sample in cap_data][0 : num_output_samples]
        q_data = [sample[1] for sample in cap_data][0 : num_output_samples]
        e7s.plot_graph(sampling_rate, i_data, 'capture data I head', dirpath + 'capture_data_i.png')
        e7s.plot_graph(sampling_rate, q_data, 'capture data Q head', dirpath + 'capture_data_q.png')


def output_spectrum(cap_unit_to_spectrum, sampling_rate):
    for cap_unit, spectrum in cap_unit_to_spectrum.items():
        dirpath = 'plot_capture_data/Capture_{}/'.format(cap_unit)
        os.makedirs(dirpath, exist_ok=True)
        i_spectrum = [abs(val) for val in spectrum.i]
        e7s.plot_spectrum(
            i_spectrum,
            'I data spectrum',
            dirpath + 'i_spectrum.png', 
            sampling_rate,
            (0, 0.1),
            0.1)
        q_spectrum = [abs(val) for val in spectrum.q]
        e7s.plot_spectrum(
            q_spectrum,
            'Q data spectrum',
            dirpath + 'q_spectrum.png', 
            sampling_rate,
            (0, 0.1),
            0.1)


def setup_dacs(rfdc_ctrl, mixer_freq):
    """DAC の設定を行う"""
    for tile in list(e7sz.DacTile):
        # FIFO 無効化
        rfdc_ctrl.disable_dac_fifo(tile)
        for channel in list(e7sz.DacChannel):
            # ミキサの設定 
            rfdc_ctrl.set_dac_mixer_settings(tile, channel, mixer_freq, 0, e7sz.MixerScale.V0P7)
            # DAC 割り込みクリア
            rfdc_ctrl.clear_dac_interrupts(tile, channel, *list(e7sz.RfdcInterrupt))
            # DAC 割り込み有効化
            rfdc_ctrl.enable_dac_interrupts(tile, channel, *list(e7sz.RfdcInterrupt))
        # FIFO 有効化
        rfdc_ctrl.enable_dac_fifo(tile)


def setup_adcs(rfdc_ctrl, mixer_freq):
    """ADC の設定を行う"""
    for tile in list(e7sz.AdcTile):
        # FIFO 無効化
        rfdc_ctrl.disable_adc_fifo(tile)
        for channel in list(e7sz.AdcChannel):
            # ミキサを無効化
            rfdc_ctrl.set_adc_mixer_settings(tile, channel, True, mixer_freq, 0, e7sz.MixerScale.V0P7)
            # ADC 割り込みクリア
            rfdc_ctrl.clear_adc_interrupts(tile, channel, *list(e7sz.RfdcInterrupt))
            # ADC 割り込み有効化
            rfdc_ctrl.enable_adc_interrupts(tile, channel, *list(e7sz.RfdcInterrupt))
        # FIFO 有効化
        rfdc_ctrl.enable_adc_fifo(tile)


def get_dac_interrupts(rfdc_ctrl):
    """全ての DAC の割り込みを取得する"""
    dac_to_interrupts = {}
    for tile in list(e7sz.DacTile):
        dac_to_interrupts[tile] = {}
        for channel in list(e7sz.DacChannel):
            dac_to_interrupts[tile][channel] = rfdc_ctrl.get_dac_interrupts(tile, channel)
    
    return dac_to_interrupts


def get_adc_interrupts(rfdc_ctrl):
    """全ての ADC の割り込みを取得する"""
    adc_to_interrupts = {}
    for tile in list(e7sz.AdcTile):
        adc_to_interrupts[tile] = {}
        for channel in list(e7sz.AdcChannel):
            adc_to_interrupts[tile][channel] = rfdc_ctrl.get_adc_interrupts(tile, channel)
    
    return adc_to_interrupts


def get_capture_data(cap_ctrl, cap_unit_to_cap_param):
    cap_unit_to_cap_data = {}
    for cap_unit, cap_param in cap_unit_to_cap_param.items():
        cap_unit_to_cap_data[cap_unit] = cap_ctrl.get_capture_data(cap_unit, cap_param)

    return cap_unit_to_cap_data


def calc_spectrum(cap_unit_to_cap_data, num_fft_samples):
    cap_unit_to_spectrum = {}
    for cap_unit, cap_data in cap_unit_to_cap_data.items():
        i_data = [sample[0] for sample in cap_data[0 : num_fft_samples]]
        q_data = [sample[1] for sample in cap_data[0 : num_fft_samples]]
        cap_unit_to_spectrum[cap_unit] = IqSpectrum(np.fft.fft(i_data), np.fft.fft(q_data))

    return cap_unit_to_spectrum


def output_dac_interrupt_details(dac_to_interrupts):
    """RF Data Converter の DAC の割り込みを出力する"""
    for tile, channel_to_interrupts in dac_to_interrupts.items():
        for channel, interrupts in channel_to_interrupts.items():
            if len(interrupts) != 0:
                print('Interrupts on DAC tile {}, channel {}'.format(tile, channel))
            for interrupt in interrupts:
                print('  ', e7sz.RfdcInterrupt.to_msg(interrupt))


def output_adc_interrupt_details(adc_to_interrupts):
    """RF Data Converter の DAC の割り込みを出力する"""
    for tile, channel_to_interrupts in adc_to_interrupts.items():
        for channel, interrupts in channel_to_interrupts.items():
            if len(interrupts) != 0:
                print('Interrupts on ADC tile {}, channel {}'.format(tile, channel))
            for interrupt in interrupts:
                print('  ', e7sz.RfdcInterrupt.to_msg(interrupt))


def main(
    design_type,
    cap_unit_to_awg,
    ip_addr,
    awg_to_wave_chunks,
    num_wait_words,
    capture_delay,
    dac_mixer_freq, 
    adc_mixer_freq,
    num_fft_samples,
    num_output_wave_samples,
    num_output_capture_samples,
    timeout):
    hw_specs = e7s.E7AwgHwSpecs(design_type)
    awgs = list(cap_unit_to_awg.values())
    cap_units = list(cap_unit_to_awg.keys())
    with (e7sz.RftoolTransceiver(ip_addr.zcu111, 15) as transceiver,
          e7sz.RfdcCtrl(transceiver, design_type) as rfdc_ctrl,
          e7s.AwgCtrl(ip_addr.fpga, design_type) as awg_ctrl,
          bc.CaptureCtrl(ip_addr.fpga, design_type) as cap_ctrl):
        # FPGA コンフィギュレーション
        print('configure FPGA')
        e7sz.configure_fpga(transceiver, design_type)
        # ADC キャリブレーション
        print('calibrate ADCs')
        output_calibration_wave(rfdc_ctrl, awg_ctrl, awgs, hw_specs, [10e6, 25e6, 75e6, 90e6, 100e6])
        # DAC のセットアップ
        print('setup DACs')
        setup_dacs(rfdc_ctrl, dac_mixer_freq)
        # ADC のセットアップ
        print('setup ADCs')
        setup_adcs(rfdc_ctrl, adc_mixer_freq)
        # DAC / ADC タイルを同期させる.  ミキサの設定を行ってから実行する必要がある.
        print('synchronize DAC tiles and ADC tiles.')
        rfdc_ctrl.sync_dac_adc_tiles()
        # AWG のセットアップ
        print('setup AWGs')
        awg_to_wave_sequence = setup_awgs(awg_ctrl, awg_to_wave_chunks, num_wait_words, hw_specs)
        # Capture Unit のセットアップ
        print('setup Capture Units')
        cap_unit_to_cap_param = setup_capture_units(
            cap_ctrl, cap_unit_to_awg, awg_to_wave_sequence, capture_delay, hw_specs)
        # 波形送信スタート
        print('start AWGs')
        awg_ctrl.start_awgs(*awgs)
        # 波形送信完了待ち
        print('wait for AWGs to stop')
        awg_ctrl.wait_for_awgs_to_stop(timeout, *awgs)
        # キャプチャ終了待ち
        print('wait for Capture Units to stop')
        cap_ctrl.wait_for_capture_units_to_stop(timeout, *cap_units)
        # キャプチャデータ取得
        print('get capture data')
        cap_unit_to_cap_data = get_capture_data(cap_ctrl, cap_unit_to_cap_param)
        # キャプチャデータのスペクトルを計算する
        print('calculate the spectrum')
        cap_unit_to_spectrum = calc_spectrum(cap_unit_to_cap_data, num_fft_samples)
        # DAC 割り込みチェック
        print('check DAC interrupts')
        dac_to_interrupts = get_dac_interrupts(rfdc_ctrl)
        output_dac_interrupt_details(dac_to_interrupts)
        # ADC 割り込みチェック
        print('check ADC interrupts')
        adc_to_interrupts = get_adc_interrupts(rfdc_ctrl)
        output_adc_interrupt_details(adc_to_interrupts)        
        # AWG エラーチェック
        print('check awg errors')
        check_awg_err(awg_ctrl, awgs)
        # Captutre Unit エラーチェック
        print('check capture unit errors')
        check_capture_unit_err(cap_ctrl, cap_units)
        # 波形保存
        print('output AWG waveforms')
        awg_sampling_rate = hw_specs.awg.sampling_rate
        output_waveform(awg_to_wave_sequence, awg_sampling_rate, num_output_wave_samples)
        # キャプチャデータ保存
        print('output Capture Data')
        cap_sampling_rate = hw_specs.cap_units[e7s.CaptureUnit.U0].sampling_rate
        output_capture_data(cap_unit_to_cap_data, cap_sampling_rate, num_output_capture_samples)
        # スペクトル保存
        print('output the spectrum')
        output_spectrum(cap_unit_to_spectrum, cap_sampling_rate)
        print('end')


def get_program_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ipaddr', default='192.168.1.3', type=str)
    parser.add_argument('--timeout', default=5, type=int)
    parser.add_argument('--num-wait-words', default=0, type=int)
    parser.add_argument('--capture-delay', default=1.23e-7, type=float) # second
    return parser.parse_args()


if __name__ == "__main__":
    program_args = get_program_args()
    ip_addr = IpAddr(program_args.ipaddr, '10.0.0.16')

    cap_unit_to_awg = {
        e7s.CaptureUnit.U5: e7s.AWG.U0,
        e7s.CaptureUnit.U0: e7s.AWG.U6,
        e7s.CaptureUnit.U1: e7s.AWG.U7
    }
    awg_to_wave_chunks = {
        e7s.AWG.U0: [WaveChunk(25.44e6, 256, 28000, 1)],
        e7s.AWG.U6: [WaveChunk(38.16e6, 256, 28000, 1)],
        e7s.AWG.U7: [WaveChunk(50.88e6, 256, 28000, 1)]
    }

    design_type = e7s.E7AwgHwType.ZCU111_DAC_6G_URAM_X2
    num_wait_words = program_args.num_wait_words
    capture_delay = program_args.capture_delay
    dac_mixer_freq = 12.72 # MHz
    adc_mixer_freq = 38.16 # MHz
    num_fft_samples = 16384
    num_output_wave_samples = 250 # グラフに出力するユーザ定義波形のサンプル数
    num_output_capture_samples = 300 # グラフに出力するキャプチャデータのサンプル数
    timeout = program_args.timeout # second

    main(
        design_type,
        cap_unit_to_awg,
        ip_addr,
        awg_to_wave_chunks,
        num_wait_words,
        capture_delay,
        dac_mixer_freq, 
        adc_mixer_freq,
        num_fft_samples,
        num_output_wave_samples,
        num_output_capture_samples,
        timeout)
