import sys
import os
import random
import pathlib
from testutil import gen_random_int_list
import numpy as np

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from e7awgsw import AWG, AwgCtrl, WaveSequence
from e7awgsw import CaptureModule, CaptureCtrl, CaptureParam, DspUnit, CaptureUnit, DecisionFunc
from e7awgsw.labrad import RemoteAwgCtrl, RemoteCaptureCtrl
from emulator.dspmodule import dsp

class CaptureTestDsp(object):

    def __init__(self, res_dir, ip_addr, capture_modules, use_labrad, server_ip_addr):
        self.__ip_addr = ip_addr
        self.__server_ip_addr = server_ip_addr
        self.__use_labrad = use_labrad
        self.__res_dir = res_dir
        os.makedirs(self.__res_dir, exist_ok = True)
        # テストデザインでは, AWG 2 が Captrue 0, 1, 2, 3 に繋がっており, AWG 15 が Capture 4, 5, 6, 7 に繋がっている
        self.__awg_to_capture_module = {}
        self.__cap_units_to_test = []
        if CaptureModule.U0 in capture_modules:
            self.__awg_to_capture_module[AWG.U2] = CaptureModule.U0
            self.__cap_units_to_test += [CaptureUnit.U0, CaptureUnit.U2] # データ転送に時間がかかるのでユニット 0, 2 だけ調べる
        if CaptureModule.U1 in capture_modules:
            self.__awg_to_capture_module[AWG.U15] = CaptureModule.U1
            self.__cap_units_to_test += [CaptureUnit.U4, CaptureUnit.U7] # データ転送に時間がかかるのでユニット 4, 7 だけ調べる
        # 初期化
        with (self.__create_awg_ctrl() as awg_ctrl,
              self.__create_cap_ctrl() as cap_ctrl):
            self.__setup_modules(awg_ctrl, cap_ctrl)
    
    def __save_wave_samples(self, capture_unit_to_capture_data, test_name, filename):
        for cap_unit_id, cap_data_list in capture_unit_to_capture_data.items():
            dir = self.__res_dir + '/' + test_name
            os.makedirs(dir, exist_ok = True)
            capture_data_file = dir + '/' + filename + '_{}.txt'.format(cap_unit_id)
            self.__write_to_file(cap_data_list, capture_data_file)
        
    def __save_capture_params(self, capture_unit_to_capture_param, test_name):
        for cap_unit_id, cap_param in capture_unit_to_capture_param.items():
            dir = self.__res_dir + '/' + test_name
            os.makedirs(dir, exist_ok = True)
            capture_param_file = dir + '/captured_params_{}.txt'.format(cap_unit_id)
            with open(capture_param_file, 'w') as txt_file:
                txt_file.write(str(cap_param))

    def __write_to_file(self, cap_data_list, filepath):
        with open(filepath, 'w') as txt_file:
            for cap_data in cap_data_list:
                if isinstance(cap_data, tuple):
                    txt_file.write("{}    {}\n".format(cap_data[0], cap_data[1]))
                else:
                    txt_file.write("{}\n".format(cap_data))

    def __gen_wave_seq(self, num_samples):
        wave_seq = WaveSequence(
            num_wait_words = 32, # <- キャプチャのタイミングがズレるので変更しないこと.
            num_repeats = 1)

        num_chunk_samples = 1024 * 1024
        num_chunk_repeats = num_samples // num_chunk_samples + 1
        i_data = gen_random_int_list(num_chunk_samples, -32768, 32767)
        q_data = gen_random_int_list(num_chunk_samples, -32768, 32767)
        wave_seq.add_chunk(
            iq_samples = list(zip(i_data, q_data)),
            num_blank_words = 0, 
            num_repeats = num_chunk_repeats)

        return wave_seq

    def __save_wave_seq_params(self, awg_id, wave_seq):
        filepath = self.__res_dir + '/wave_seq_params_{}.txt'.format(awg_id)
        txt_file = open(filepath, 'w')
        txt_file.write(str(wave_seq))
        txt_file.close()

    def __gen_capture_param(self, *dsp_units):
        capture_param = CaptureParam()
        capture_param.complex_fir_coefs = [
            complex(
                random.randint(CaptureParam.MIN_FIR_COEF_VAL, CaptureParam.MAX_FIR_COEF_VAL), 
                random.randint(CaptureParam.MIN_FIR_COEF_VAL, CaptureParam.MAX_FIR_COEF_VAL))
            for _ in range(CaptureParam.NUM_COMPLEX_FIR_COEFS)]

        capture_param.real_fir_i_coefs = gen_random_int_list(
            CaptureParam.NUM_REAL_FIR_COEFS, CaptureParam.MIN_FIR_COEF_VAL, CaptureParam.MAX_FIR_COEF_VAL)
        capture_param.real_fir_q_coefs = gen_random_int_list(
            CaptureParam.NUM_REAL_FIR_COEFS, CaptureParam.MIN_FIR_COEF_VAL, CaptureParam.MAX_FIR_COEF_VAL)

        capture_param.complex_window_coefs = [
            complex(
                random.randint(CaptureParam.MIN_WINDOW_COEF_VAL, CaptureParam.MAX_WINDOW_COEF_VAL), 
                random.randint(CaptureParam.MIN_WINDOW_COEF_VAL, CaptureParam.MAX_WINDOW_COEF_VAL))
            for _ in range(CaptureParam.NUM_COMPLEXW_WINDOW_COEFS)]

        max_sum_sec_len = 120
        capture_param.sum_start_word_no = 0
        capture_param.num_words_to_sum = random.randint(1, max_sum_sec_len)

        # sum 無し, integ あり
        if (DspUnit.INTEGRATION in dsp_units) and (not DspUnit.SUM in dsp_units):
            num_sum_sections = 4096 // max_sum_sec_len
            capture_param.num_integ_sections = 1024
        # sum あり, integ あり
        elif (DspUnit.INTEGRATION in dsp_units) and (DspUnit.SUM in dsp_units):
            num_sum_sections = 4096
            capture_param.num_integ_sections = 5
        else:
            num_sum_sections = 512
            capture_param.num_integ_sections = 4
        for _ in range(num_sum_sections):
            # 総和区間長が 3 ワード以下の場合 decimation から値が出てこなくなるので 4 ワード以上を指定する
            capture_param.add_sum_section(random.randint(4, max_sum_sec_len), random.randint(1, 24))

        a0 = np.float32(random.randint(CaptureParam.MIN_DECISION_FUNC_COEF_VAL, CaptureParam.MAX_DECISION_FUNC_COEF_VAL))
        b0 = np.float32(random.randint(CaptureParam.MIN_DECISION_FUNC_COEF_VAL, CaptureParam.MAX_DECISION_FUNC_COEF_VAL))
        c0 = np.float32(random.randint(-10000, 10000))
        capture_param.set_decision_func_params(DecisionFunc.U0, a0, b0, c0)
        capture_param.set_decision_func_params(DecisionFunc.U1, b0, -a0, -c0)

        return capture_param

    def __setup_modules(self, awg_ctrl, cap_ctrl):
        awg_ctrl.initialize(*self.__awg_to_capture_module.keys())
        cap_ctrl.initialize(*self.__cap_units_to_test)
        # キャプチャモジュールをスタートする AWG の設定
        for awg_id, cap_mod in self.__awg_to_capture_module.items():
            cap_ctrl.select_trigger_awg(cap_mod, awg_id)
        # スタートトリガの有効化
        cap_ctrl.enable_start_trigger(*self.__cap_units_to_test)

    def __set_wave_sequence(self, awg_ctrl, capture_unit_to_capture_param):
        max_samples = 0
        for param in capture_unit_to_capture_param.values():
            max_samples = max(max_samples, param.num_samples_to_process)

        awg_to_wave_sequence = {}
        for awg_id in self.__awg_to_capture_module.keys():
            wave_seq = self.__gen_wave_seq(max_samples)
            awg_to_wave_sequence[awg_id] = wave_seq
            awg_ctrl.set_wave_sequence(awg_id, wave_seq)
        return awg_to_wave_sequence        

    def __get_capture_data(self, cap_ctrl, cls_result):
        capture_unit_to_capture_data = {}
        for capture_unit_id in self.__cap_units_to_test:
            num_captured_samples = cap_ctrl.num_captured_samples(capture_unit_id)
            if cls_result:
                capture_unit_to_capture_data[capture_unit_id] = \
                    cap_ctrl.get_classification_results(capture_unit_id, num_captured_samples)
            else:
                capture_unit_to_capture_data[capture_unit_id] = \
                    cap_ctrl.get_capture_data(capture_unit_id, num_captured_samples)
        return capture_unit_to_capture_data

    def __calc_exp_data(self, awg_to_wave_sequence, capture_unit_to_capture_param):
        capture_unit_to_exp_data = {}
        for awg_id, wave_seq in awg_to_wave_sequence.items():
            capmod_id = self.__awg_to_capture_module[awg_id]
            for cap_unit_id in CaptureModule.get_units(capmod_id):
                if cap_unit_id in capture_unit_to_capture_param.keys():
                    param = capture_unit_to_capture_param[cap_unit_id]
                    samples = wave_seq.all_samples(False)
                    capture_unit_to_exp_data[cap_unit_id] = dsp(samples, param)
        return capture_unit_to_exp_data        

    def __set_capture_params(self, cap_ctrl, *dsp_units):
        # キャプチャパラメータの作成
        capture_unit_to_capture_param = {
            capture_unit_id : self.__gen_capture_param(*dsp_units)
            for capture_unit_id in self.__cap_units_to_test}
        # キャプチャパラメータ設定
        for capture_unit_id, capture_param in capture_unit_to_capture_param.items():
            capture_param.sel_dsp_units_to_enable(*dsp_units)
            cap_ctrl.set_capture_params(capture_unit_id, capture_param)
        return capture_unit_to_capture_param

    def __create_awg_ctrl(self):
        if self.__use_labrad:
            return RemoteAwgCtrl(self.__server_ip_addr, self.__ip_addr)
        else:
            return AwgCtrl(self.__ip_addr)

    def __create_cap_ctrl(self):
        if self.__use_labrad:
            return RemoteCaptureCtrl(self.__server_ip_addr, self.__ip_addr)
        else:
            return CaptureCtrl(self.__ip_addr)


    def run_test(self, test_name, *dsp_units):
        with (self.__create_awg_ctrl() as awg_ctrl,
              self.__create_cap_ctrl() as cap_ctrl):
            capture_unit_to_capture_param = self.__set_capture_params(cap_ctrl, *dsp_units)
            # 波形シーケンスの設定
            awg_to_wave_sequence = self.__set_wave_sequence(awg_ctrl, capture_unit_to_capture_param)
            # 波形送信スタート
            awg_ctrl.start_awgs(*self.__awg_to_capture_module.keys())
            # 波形送信完了待ち
            awg_ctrl.wait_for_awgs_to_stop(10, *self.__awg_to_capture_module.keys())
            # キャプチャ完了待ち
            cap_ctrl.wait_for_capture_units_to_stop(2400, *self.__cap_units_to_test)
            # キャプチャデータ取得
            print('get capture data')
            cls_result = DspUnit.CLASSIFICATION in dsp_units
            capture_unit_to_capture_data = self.__get_capture_data(cap_ctrl, cls_result)
            # エラーチェック
            awg_errs = awg_ctrl.check_err(*self.__awg_to_capture_module.keys())
            cap_errs = cap_ctrl.check_err(*self.__cap_units_to_test)
            if awg_errs:
                print(awg_errs)
            if cap_errs:
                print(cap_errs)

        # キャプチャデータ期待値取得
        print('calc expected value')
        capture_unit_to_exp_data = self.__calc_exp_data(awg_to_wave_sequence, capture_unit_to_capture_param)
        # キャプチャデータが DSP の結果の期待値と一致しているかチェック
        all_match = True
        for capture_unit_id in self.__cap_units_to_test:
            capture_data = capture_unit_to_capture_data[capture_unit_id]
            exp_data = capture_unit_to_exp_data[capture_unit_id]
            if exp_data != capture_data:
                all_match = False

        # 波形データを保存
        print('save wave data')
        self.__save_wave_samples(capture_unit_to_capture_data, test_name, 'captured'.format(test_name))
        self.__save_wave_samples(capture_unit_to_exp_data, test_name, 'expected'.format(test_name))
        self.__save_capture_params(capture_unit_to_capture_param, test_name)
        
        if awg_errs or cap_errs:
            return False

        return all_match
