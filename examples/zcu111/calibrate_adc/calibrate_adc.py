"""
ADC をキャリブレーションする
"""
import os
import math
import argparse
import e7awgsw as e7s
import e7awgsw.zcu111 as e7sz
import e7awgsw.basiccapture as bc


def gen_cos_wave(num_cycles, freq, amp, hw_specs):
    """
    freq : Hz
    """
    samples = e7s.SinWave(num_cycles, freq, amp, phase = math.pi / 2) \
        .gen_samples(hw_specs.awg.sampling_rate)
    # 波形データに 0 データを足して, その長さを波形パートを構成可能なサンプル数の最小単位の倍数に合わせる.
    reminder = len(samples) % hw_specs.awg.smallest_unit_of_wave_len
    if reminder != 0:
        zeros = [0] * (hw_specs.awg.smallest_unit_of_wave_len - reminder)
        samples.extend(zeros)
    return samples


def setup_dacs(rfdc_ctrl):
    for tile in list(e7sz.DacTile):
        # FIFO 無効化
        rfdc_ctrl.disable_dac_fifo(tile)
        for channel in list(e7sz.DacChannel):
            # 周波数 = 0 [MHz], 初期位相 = 0 [degrees], 振幅 = 0.7
            rfdc_ctrl.set_dac_mixer_settings(tile, channel, 0, 0, e7sz.MixerScale.V0P7)
        # FIFO 有効化
        rfdc_ctrl.enable_dac_fifo(tile)


def gen_wave_seq(freq, hw_specs):
    wave_seq = e7s.WaveSequence(
        num_wait_words = 0,
        num_repeats = 1,
        design_type = hw_specs.design_type)
    amplitude = 28000
    # pg269 v2.6 p.87 にある ADC キャリブレーションにかかる時間 (サンプリング周期の 2^20 ~ 2^22 倍) と
    # ADC の最低サンプリング周波数 (1 Gsps) から, キャリブレーション用の波形を周波数ごとに 4 ms 程度出力すれば十分と考えたが, 
    # デザイン 4 ではノイズの少ない波形をキャプチャするのに 1 波形当たり 200 ms 程度キャリブレーション時間を要したので, この値を使用する.
    wave_len = 0.2 # second
    num_cycles_in_chunk = 10
    num_cycles = max(int(freq * wave_len), num_cycles_in_chunk)
    num_chunk_repeats = num_cycles // num_cycles_in_chunk
    i_samples = gen_cos_wave(num_cycles_in_chunk, freq, amplitude, hw_specs)
    q_samples = [0] * len(i_samples)
    wave_seq.add_chunk(
        iq_samples = list(zip(i_samples, q_samples)),
        num_blank_words = 1,
        num_repeats = num_chunk_repeats)
        
    return wave_seq


def enable_calibration_adjustment(rfdc_ctrl):
    """ADC キャリブレーションのパラメータ調整を有効化する"""
    for tile in list(e7sz.AdcTile):
        for channel in list(e7sz.AdcChannel):
            rfdc_ctrl.enable_adc_calibration_adjustment(tile, channel)


def disable_calibration_adjustment(rfdc_ctrl):
    """ADC キャリブレーションのパラメータ調整を無効化する"""
    for tile in list(e7sz.AdcTile):
        for channel in list(e7sz.AdcChannel):
            rfdc_ctrl.disable_adc_calibration_adjustment(tile, channel)


def output_calibration_wave(rfdc_ctrl, awg_ctrl, awgs, hw_specs, freq_list):
    """ADC をキャリブレーションするための波形を出力する"""
    setup_dacs(rfdc_ctrl)
    awg_ctrl.initialize(*awgs)
    enable_calibration_adjustment(rfdc_ctrl)
    for freq in freq_list:
        wave_seq = gen_wave_seq(freq, hw_specs)
        for awg_id in awgs:
            awg_ctrl.set_wave_sequence(awg_id, wave_seq)
        awg_ctrl.start_awgs(*awgs)
        awg_ctrl.wait_for_awgs_to_stop(3, *awgs)
    disable_calibration_adjustment(rfdc_ctrl)
