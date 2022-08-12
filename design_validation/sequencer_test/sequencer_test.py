import sys
import os
import pathlib
import argparse
import testutil
import random
import time
import numpy as np
from paramloadtest import ParamLoadTest
from feedbackvaltest import FeedbackValTest
from waitflagtest import WaitFlagTest

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from e7awgsw import CaptureModule, WaveSequence, CaptureParam, DspUnit, DecisionFunc, CaptureParamElem


def gen_random_iq_samples(num_words):
    num_samples = WaveSequence.NUM_SAMPLES_IN_AWG_WORD * num_words
    i_data = testutil.gen_random_int_list(num_samples, -32768, 32767)
    q_data = testutil.gen_random_int_list(num_samples, -32768, 32767)
    return list(zip(i_data, q_data))


def gen_wave_sequence_0():
    wave_seq = WaveSequence(
        num_wait_words = 16, # <- キャプチャのタイミングがズレるので変更しないこと.
        num_repeats = 1)
    for i in range(16):
        wave_seq.add_chunk(
            iq_samples = gen_random_iq_samples(64),
            num_blank_words = i + 80,
            num_repeats = 1)

    return wave_seq


def gen_wave_sequence_1():
    wave_seq = WaveSequence(
        num_wait_words = 16, # <- キャプチャのタイミングがズレるので変更しないこと.
        num_repeats = 2)
    wave_seq.add_chunk(
        iq_samples = gen_random_iq_samples(128),
        num_blank_words = 10,
        num_repeats = 3)
    wave_seq.add_chunk(
        iq_samples = gen_random_iq_samples(192),
        num_blank_words = 15,
        num_repeats = 2)
    wave_seq.add_chunk(
        iq_samples = gen_random_iq_samples(256),
        num_blank_words = 20,
        num_repeats = 1)

    return wave_seq


def gen_capture_param_0():
    param = CaptureParam()
    param.num_integ_sections = 1
    for i in range(6):
        param.add_sum_section(64 + i * 128, i + 10)

    param.sel_dsp_units_to_enable(
        DspUnit.COMPLEX_FIR,
        DspUnit.DECIMATION,
        DspUnit.REAL_FIR,
        DspUnit.COMPLEX_WINDOW,
        DspUnit.SUM,
        DspUnit.INTEGRATION)
    param.capture_delay = 0
    param.complex_fir_coefs = [complex(i, 2 * i) for i in range(CaptureParam.NUM_COMPLEX_FIR_COEFS)]
    param.real_fir_i_coefs = [3 * i for i in range(CaptureParam.NUM_REAL_FIR_COEFS)]
    param.real_fir_q_coefs = [4 * i for i in range(CaptureParam.NUM_REAL_FIR_COEFS)]
    param.complex_window_coefs = [complex(5 * i, 6 * i) for i in range(CaptureParam.NUM_COMPLEXW_WINDOW_COEFS)]
    param.set_decision_func_params(DecisionFunc.U0, np.float32(1), np.float32(1), np.float32(0))
    param.set_decision_func_params(DecisionFunc.U1, np.float32(-1), np.float32(1), np.float32(0))
    return param


def gen_capture_param_1():
    param = CaptureParam()
    param.num_integ_sections = 2
    for i in range(7):
        param.add_sum_section(128 + i * 8, i + 5)

    param.sum_start_word_no = 4
    param.num_words_to_sum = 480
    param.capture_delay = 0
    param.complex_fir_coefs = [complex(7, 8 * i) for i in range(CaptureParam.NUM_COMPLEX_FIR_COEFS)]
    param.real_fir_i_coefs = [9 * i for i in range(CaptureParam.NUM_REAL_FIR_COEFS)]
    param.real_fir_q_coefs = [10 * i for i in range(CaptureParam.NUM_REAL_FIR_COEFS)]
    param.complex_window_coefs = [complex(11 * i, 12 * i) for i in range(CaptureParam.NUM_COMPLEXW_WINDOW_COEFS)]
    param.set_decision_func_params(DecisionFunc.U0, np.float32(-1), np.float32(1), np.float32(0))
    param.set_decision_func_params(DecisionFunc.U1, np.float32(1), np.float32(1), np.float32(0))
    return param


def gen_capture_param_2():
    param = CaptureParam()
    param.num_integ_sections = 3
    for i in range(3):
        param.add_sum_section(64 + i * 128, i + 15)

    param.sel_dsp_units_to_enable(DspUnit.CLASSIFICATION)
    param.capture_delay = 0
    param.set_decision_func_params(DecisionFunc.U0, np.float32(1), np.float32(1), np.float32(0))
    param.set_decision_func_params(DecisionFunc.U1, np.float32(-1), np.float32(1), np.float32(0))
    return param


def main(
    num_tests,
    capture_modules,
    awg_cap_ip_addr,
    seq_ip_addr,
    server_ip_addr,
    use_labrad,
    res_dir):
    random.seed(10)
    
    # 0 以外のキャプチャディレイは, DSP エミュレータが未対応なので,
    # 本テストではシーケンサコマンドによる設定が可能かどうかチェックしない.
    # キャプチャディレイをシーケンサコマンドから設定できることは HDL シミュレーションでテスト済み.
    
    wave_sequences = [gen_wave_sequence_0(), gen_wave_sequence_1()]
    cap_params = [gen_capture_param_0(), gen_capture_param_1(), gen_capture_param_2()]
    
    failed_tests = []
    for test_id in range(num_tests):
        print("\n---- test {:03d} / {:03d} ----".format(test_id, num_tests - 1))
        res_dir = 'result/{:03d}'.format(test_id)
        test = ParamLoadTest(res_dir, awg_cap_ip_addr, seq_ip_addr, server_ip_addr, use_labrad)

        print('-- dsp units　--')
        result = test.run_test(
            'dsp_units',
            wave_sequences[0],
            wave_sequences[1],
            cap_params[0],
            cap_params[1],
            CaptureParamElem.DSP_UNITS)
        if not result:
            print('failure dsp units')
            failed_tests.append('{} - dsp units'.format(test_id))
        
        print('\n-- num integ sections --')
        result = test.run_test(
            'num_integ_sections',
            wave_sequences[0],
            wave_sequences[1],
            cap_params[0],
            cap_params[1],        
            CaptureParamElem.NUM_INTEG_SECTIONS)
        if not result:
            print('num integ sections')
            failed_tests.append('{} - num integ sections'.format(test_id))

        print('\n-- num sum sections --')
        result = test.run_test(
            'num_sum_sections',
            wave_sequences[0],
            wave_sequences[1],
            cap_params[1],
            cap_params[0],    
            CaptureParamElem.NUM_SUM_SECTIONS)
        if not result:
            print('failure num sum sections')
            failed_tests.append('{} - num sum sections'.format(test_id))

        print('\n-- sum target interval --')
        result = test.run_test(
            'sum_target_interval',
            wave_sequences[0],
            wave_sequences[1],
            cap_params[0],
            cap_params[1],        
            CaptureParamElem.SUM_TARGET_INTERVAL)
        if not result:
            print('failure sum target interval')
            failed_tests.append('{} - sum target interval'.format(test_id))

        print('\n-- sum section len --')
        result = test.run_test(
            'sum_section_len',
            wave_sequences[0],
            wave_sequences[1],
            cap_params[0],
            cap_params[1],        
            CaptureParamElem.SUM_SECTION_LEN)
        if not result:
            print('failure sum section len')
            failed_tests.append('{} - sum section len'.format(test_id))

        print('\n-- post blank len --')
        result = test.run_test(
            'post_blank_len',
            wave_sequences[0],
            wave_sequences[1],
            cap_params[0],
            cap_params[1],        
            CaptureParamElem.POST_BLANK_LEN)
        if not result:
            print('failure post blank len')
            failed_tests.append('{} - post blank len'.format(test_id))

        print('\n-- comp fir coef --')
        result = test.run_test(
            'comp_fir_coef',
            wave_sequences[0],
            wave_sequences[1],
            cap_params[0],
            cap_params[1],        
            CaptureParamElem.COMP_FIR_COEF)
        if not result:
            print('failure comp fir coef')
            failed_tests.append('{} - comp fir coef'.format(test_id))

        print('\n-- real fir coef --')
        result = test.run_test(
            'real_fir_coef',
            wave_sequences[0],
            wave_sequences[1],
            cap_params[0],
            cap_params[1],        
            CaptureParamElem.REAL_FIR_COEF)
        if not result:
            print('failure real fir coef')
            failed_tests.append('{} - real fir coef'.format(test_id))

        print('\n-- comp window coef --')
        result = test.run_test(
            'comp_window_coef',
            wave_sequences[0],
            wave_sequences[1],
            cap_params[0],
            cap_params[1],        
            CaptureParamElem.COMP_WINDOW_COEF)
        if not result:
            print('failure comp window coef')
            failed_tests.append('{} - comp window coef'.format(test_id))

        print('\n-- dicision func param --')
        result = test.run_test(
            'dicision_func_param',
            wave_sequences[0],
            wave_sequences[1],
            cap_params[2],
            cap_params[1],
            CaptureParamElem.DICISION_FUNC_PARAM)
        if not result:
            print('failure dicision func param')
            failed_tests.append('{} - comp dicision func param'.format(test_id))

        print('\n-- sum section set --')
        result = test.run_test(
            'sum_section_set',
            wave_sequences[0],
            wave_sequences[1],
            cap_params[0],
            cap_params[1],
            CaptureParamElem.NUM_INTEG_SECTIONS,
            CaptureParamElem.NUM_SUM_SECTIONS,
            CaptureParamElem.SUM_SECTION_LEN,
            CaptureParamElem.POST_BLANK_LEN,
            CaptureParamElem.SUM_TARGET_INTERVAL)
        if not result:
            print('failure sum section set')
            failed_tests.append('{} - comp sum section set'.format(test_id))

        print('\n-- dsp set --')
        result = test.run_test(
            'dsp_set',
            wave_sequences[0],
            wave_sequences[0],
            cap_params[1],
            cap_params[0],
            CaptureParamElem.DSP_UNITS,
            CaptureParamElem.COMP_FIR_COEF,
            CaptureParamElem.REAL_FIR_COEF,
            CaptureParamElem.COMP_WINDOW_COEF)
        if not result:
            print('failure dsp set')
            failed_tests.append('{} - dsp set'.format(test_id))

        print('\n-- all elems --')
        result = test.run_test(
            'all_elems',
            wave_sequences[0],
            wave_sequences[0],
            cap_params[1],
            cap_params[0],
            *CaptureParamElem.all())
        if not result:
            print('failure all elems')
            failed_tests.append('{} - all elems'.format(test_id))

        test.close()

        print('\n-- feedback val test --')
        test = FeedbackValTest(res_dir, awg_cap_ip_addr, seq_ip_addr, server_ip_addr, use_labrad)
        result = test.run_test('feedback_val_test')
        test.close()
        if not result:
            print('failure feedback val test')
            failed_tests.append('{} - feedback val test'.format(test_id))


        test = WaitFlagTest(res_dir, awg_cap_ip_addr, seq_ip_addr, server_ip_addr, use_labrad)
        result = test.run_test()
        test.close()
        if not result:
            print('failure wait flag test')
            failed_tests.append('{} - wait flag test'.format(test_id))

    if failed_tests:
        for test_id in failed_tests:
            print("Test {} failed.".format(test_id))
    else:
        print("All tests succeeded.".format(failed_tests))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--num-tests', default=1, type=int)
    parser.add_argument('--capture-module')
    parser.add_argument('--ipaddr', default='10.1.0.255')
    parser.add_argument('--server-ipaddr', default='localhost')
    parser.add_argument('--seq-ipaddr', default='10.2.0.255')
    parser.add_argument('--labrad', action='store_true')
    parser.add_argument('--result-dir', default='result')
    args = parser.parse_args()

    capture_modules = CaptureModule.all()
    if args.capture_module is not None:
        capture_modules = [CaptureModule.of(int(args.capture_module))]

    main(
        args.num_tests,
        capture_modules,
        args.ipaddr,
        args.seq_ipaddr,
        args.server_ipaddr,
        args.labrad,
        args.result_dir)
