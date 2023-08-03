import sys
import os
import copy
import numpy as np
import pathlib

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)

from e7awgsw.memorymap import CaptureParamRegs
from e7awgsw.hwparam import NUM_SAMPLES_IN_AWG_WORD, NUM_SAMPLES_IN_CAP_RAM_WORD, NUM_CLS_RESULTS_IN_CAP_RAM_WORD
from e7awgsw import CaptureParam, DecisionFunc


def output_wave_sequences(awg_to_wave_seq, dir, filename):
    os.makedirs(dir, exist_ok = True)
    for awg_id, wave_seq in awg_to_wave_seq.items():
        filepath = dir + '/' + filename + '_{}.txt'.format(awg_id)
        with open(filepath, 'w') as txt_file:
            _write_awg_words(txt_file, wave_seq.all_samples_lazy(False))


def _write_awg_words(file, samples):
    for i in range(0, len(samples), NUM_SAMPLES_IN_AWG_WORD):
        if i % 64 == 0:
            sideband = 1
        elif i % 64 == 60:
            sideband = 2
        else:
            sideband = 0

        awg_word = 0
        for j in range(NUM_SAMPLES_IN_AWG_WORD):
            iq = samples[i + j]
            awg_word |= (0xFFFF & iq[0]) << (j * 32)
            awg_word |= (0xFFFF & iq[1]) << (j * 32 + 16)

        file.write('{}{:032X}\n'.format(sideband, awg_word))


def output_capture_samples(cap_unit_to_cap_data, dir, filename):
    os.makedirs(dir, exist_ok = True)
    cap_unit_to_cap_data = copy.deepcopy(cap_unit_to_cap_data)
    for cap_id, samples in cap_unit_to_cap_data.items():
        filepath = dir + '/' + filename + '_{}.txt'.format(cap_id)
        _add_zero(samples)
        is_cls_data = not isinstance(samples[0], tuple)
        with open(filepath, 'w') as txt_file:
            # 四値化データ
            if is_cls_data:
                _write_cls_cap_words(txt_file, samples)
            # I/Q データ
            else:
                _write_iq_cap_words(txt_file, samples)


def _add_zero(samples):
    is_cls_data = not isinstance(samples[0], tuple)
    if is_cls_data:
        NUM_SAMPLES_IN_BURST_WORDS = NUM_CLS_RESULTS_IN_CAP_RAM_WORD * 16
        rem = len(samples) % NUM_SAMPLES_IN_BURST_WORDS
        if rem != 0:
            num_additional_samples = NUM_SAMPLES_IN_BURST_WORDS - rem
            samples += [0] * num_additional_samples
    else:
        NUM_SAMPLES_IN_BURST_WORDS = NUM_SAMPLES_IN_CAP_RAM_WORD * 16
        rem = len(samples) % NUM_SAMPLES_IN_BURST_WORDS
        if rem != 0:
            num_additional_samples = NUM_SAMPLES_IN_BURST_WORDS - rem
            samples += [(0.0, 0.0)] * num_additional_samples
    

def _write_iq_cap_words(file, samples):
    for i in range(0, len(samples), NUM_SAMPLES_IN_CAP_RAM_WORD):
        capture_word = 0
        for j in range(NUM_SAMPLES_IN_CAP_RAM_WORD):
            iq = samples[i + j]
            capture_word |= int.from_bytes(np.float32(iq[0]).tobytes(), 'little') << (j * 64)
            capture_word |= int.from_bytes(np.float32(iq[1]).tobytes(), 'little') << (j * 64 + 32)
        file.write('{:064X}\n'.format(capture_word))


def _write_cls_cap_words(file, samples):
    for i in range(0, len(samples), NUM_CLS_RESULTS_IN_CAP_RAM_WORD):
        capture_word = 0
        for j in range(NUM_CLS_RESULTS_IN_CAP_RAM_WORD):
            capture_word |= samples[i + j] << (j * 2)
        file.write('{:064X}\n'.format(capture_word))


def output_capture_params(cap_unit_to_cap_params, dir, filename):
    os.makedirs(dir, exist_ok = True)
    for cap_id, params in cap_unit_to_cap_params.items():
        filepath = dir + '/' + filename + '_{}.txt'.format(cap_id)
        with open(filepath, 'w') as txt_file:
            _write_capture_section_params(txt_file, params)
            _write_complex_fir_coefs(txt_file, params)
            _write_real_fir_coefs(txt_file, params)
            _write_complex_window_coefs(txt_file, params)
            _write_decision_func_params(txt_file, params)


def _write_capture_section_params(file, params):
    val = 0
    for dsp_unit in params.dsp_units_enabled:
        val |= 1 << dsp_unit
    val |= params.capture_delay << 32
    val |= params.num_integ_sections << 128
    val |= params.num_sum_sections << 160
    val |= params.sum_start_word_no << 192
    end_start_word_no = min(
        params.sum_start_word_no + params.num_words_to_sum - 1,
        CaptureParam.MAX_SUM_SECTION_LEN)
    val |= end_start_word_no << 224
    file.write('{:05X} {:064X}\n'.format(CaptureParamRegs.Offset.DSP_MODULE_ENABLE, val))
    _write_sum_sec_params(file, params)


def _write_sum_sec_params(file, params):
    sum_sec_len_list = params.sum_section_list
    rem = params.num_sum_sections % 8
    if rem != 0:
        sum_sec_len_list += [(0, 0)] * (8 - rem)

    for i in range(0, len(sum_sec_len_list), 8):
        val = 0
        for j in range(8):
            val |= sum_sec_len_list[i + j][0] << (j * 32)
        file.write(
            '{:05X} {:064X}\n'.format(CaptureParamRegs.Offset.sum_section_length(i), val))

    for i in range(0, len(sum_sec_len_list), 8):
        val = 0
        for j in range(8):
            val |= sum_sec_len_list[i + j][1] << (j * 32)
        file.write(
            '{:05X} {:064X}\n'.format(CaptureParamRegs.Offset.post_blank_length(i), val))


def _write_complex_fir_coefs(file, params):
    coefs = params.complex_fir_coefs
    for i in range(0, CaptureParam.NUM_COMPLEX_FIR_COEFS, 8):
        val = 0
        for j in range(8):
            val |= (0xFFFF & int(coefs[i + j].real)) << (j * 32)
        file.write(
            '{:05X} {:064X}\n'.format(CaptureParamRegs.Offset.comp_fir_re_coef(i), val))
    
    for i in range(0, CaptureParam.NUM_COMPLEX_FIR_COEFS, 8):
        val = 0
        for j in range(8):
            val |= (0xFFFF & int(coefs[i + j].imag)) << (j * 32)
        file.write(
            '{:05X} {:064X}\n'.format(CaptureParamRegs.Offset.comp_fir_im_coef(i), val))


def _write_real_fir_coefs(file, params):
    coefs = params.real_fir_i_coefs
    val = 0
    for i in range(CaptureParam.NUM_REAL_FIR_COEFS):
        val |= (0xFFFF & int(coefs[i])) << (i * 32)
    file.write(
        '{:05X} {:064X}\n'.format(CaptureParamRegs.Offset.real_fir_i_coef(0), val))

    coefs = params.real_fir_q_coefs
    val = 0
    for i in range(CaptureParam.NUM_REAL_FIR_COEFS):
        val |= (0xFFFF & int(coefs[i])) << (i * 32)
    file.write(
        '{:05X} {:064X}\n'.format(CaptureParamRegs.Offset.real_fir_q_coef(0), val))


def _write_complex_window_coefs(file, params):
    coefs = params.complex_window_coefs
    for i in range(0, CaptureParam.NUM_COMPLEXW_WINDOW_COEFS, 8):
        val = 0
        for j in range(8):
            val |= (0xFFFFFFFF & int(coefs[i + j].real)) << (j * 32)
        file.write(
            '{:05X} {:064X}\n'.format(CaptureParamRegs.Offset.comp_window_re_coef(i), val))

    for i in range(0, CaptureParam.NUM_COMPLEXW_WINDOW_COEFS, 8):
        val = 0
        for j in range(8):
            val |= (0xFFFFFFFF & int(coefs[i + j].imag)) << (j * 32)
        file.write(
            '{:05X} {:064X}\n'.format(CaptureParamRegs.Offset.comp_window_im_coef(i), val))


def _write_decision_func_params(file, params):
    a0, b0, c0 = params.get_decision_func_params(DecisionFunc.U0)
    a1, b1, c1 = params.get_decision_func_params(DecisionFunc.U1)
    file.write('{:05X} {:016X}{:08X}{:08X}{:08X}{:08X}{:08X}{:08X}\n'.format(
        CaptureParamRegs.Offset.decision_func_params(0),
        0,
        int.from_bytes(c1.tobytes(), 'little'),
        int.from_bytes(b1.tobytes(), 'little'),
        int.from_bytes(a1.tobytes(), 'little'),
        int.from_bytes(c0.tobytes(), 'little'),
        int.from_bytes(b0.tobytes(), 'little'),
        int.from_bytes(a0.tobytes(), 'little')))
