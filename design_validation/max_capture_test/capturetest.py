import sys
import os
import pathlib
import numpy as np
import random
from testutil import gen_random_int_list

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from e7awgsw import AWG, AwgCtrl, WaveSequence
from e7awgsw import DspUnit, CaptureUnit, CaptureModule, DecisionFunc, CaptureCtrl, CaptureParam
from e7awgsw.labrad import RemoteAwgCtrl, RemoteCaptureCtrl
from e7awgsw import hwparam
from emulator.dspmodule import classification, fixed_to_float

class CaptureTest(object):

    def __init__(self, res_dir, ip_addr, use_labrad, server_ip_addr):
        self.__ip_addr = ip_addr
        self.__use_labrad = use_labrad
        self.__server_ip_addr = server_ip_addr
        self.__res_dir = res_dir
        # テストデザインでは, AWG 2 が Captrue 0, 1, 2, 3 に繋がっており, AWG 15 が Capture 4, 5, 6, 7 に繋がっている
        self.__awg = AWG.U2
        self.__capture_module = CaptureModule.U0
        self.__capture_units = [CaptureUnit.U3]
        os.makedirs(self.__res_dir, exist_ok = True)
    
    def __save_wave_samples(self, expected, capture_unit_to_capture_data):
        udef_wave_file = self.__res_dir + '/expected_data.txt'
        self.__write_to_file(expected, udef_wave_file)

        # キャプチャデータの最初と最後の繰り返しだけ保存する
        exp_len = len(expected)
        for cap_unit_id, cap_data in capture_unit_to_capture_data.items():
            num_repeats = len(cap_data) // exp_len
            capture_data_file = self.__res_dir + '/capture_data_{}_head.txt'.format(cap_unit_id)
            self.__write_to_file(cap_data[0:exp_len], capture_data_file)
            capture_data_file = self.__res_dir + '/capture_data_{}_tail.txt'.format(cap_unit_id)
            self.__write_to_file(cap_data[(num_repeats - 1) * exp_len:], capture_data_file)
        
    def __save_capture_params(self, capture_param):
            capture_param_file = self.__res_dir + '/capture_params.txt'
            with open(capture_param_file, 'w') as txt_file:
                txt_file.write(str(capture_param))

    def __write_to_file(self, cap_data_list, filepath):
        with open(filepath, 'w') as txt_file:
            for cap_data in cap_data_list:
                if isinstance(cap_data, tuple):
                    txt_file.write("{}    {}\n".format(cap_data[0], cap_data[1]))
                else:
                    txt_file.write("{}\n".format(cap_data))

    def __gen_wave_seq(self, do_classification):
        wave_seq = WaveSequence(
            num_wait_words = 16, # <- キャプチャのタイミングがズレるので変更しないこと.
            num_repeats = 1)

        if do_classification:
            # キャプチャ可能な最大サンプル数
            num_samples = hwparam.MAX_CAPTURE_SIZE * 8 // hwparam.CLASSIFICATION_RESULT_SIZE
        else:        
            num_samples = hwparam.MAX_CAPTURE_SIZE // hwparam.CAPTURED_SAMPLE_SIZE
        
        num_repeats = num_samples // 1024
        i_data = gen_random_int_list(num_samples // num_repeats, -32768, 32767)
        q_data = gen_random_int_list(num_samples // num_repeats, -32768, 32767)
        wave_seq.add_chunk(
            iq_samples = list(zip(i_data, q_data)),
            num_blank_words = 0, 
            num_repeats = num_repeats)

        return wave_seq

    def __save_wave_seq_params(self, awg_id, wave_seq):
        filepath = self.__res_dir + '/wave_seq_params_{}.txt'.format(awg_id)
        txt_file = open(filepath, 'w')
        txt_file.write(str(wave_seq))
        txt_file.close()

    def __convert_to_float(self, samples):
        """
        AWG が出力するサンプルを Capture がそのまま保存したときの浮動小数点データに変換する
        """
        iq_samples = []
        for i_data, q_data in samples:
            iq_samples.append((float(i_data), float(q_data)))
        return iq_samples

    def __gen_capture_param(self, wave_seq, do_classification):
        capture_param = CaptureParam()
        capture_param.num_integ_sections = 1
        capture_param.add_sum_section(wave_seq.num_all_words - wave_seq.num_wait_words, 1)
        
        a0 = np.float32(random.randint(CaptureParam.MIN_DECISION_FUNC_COEF_VAL, CaptureParam.MAX_DECISION_FUNC_COEF_VAL))
        b0 = np.float32(random.randint(CaptureParam.MIN_DECISION_FUNC_COEF_VAL, CaptureParam.MAX_DECISION_FUNC_COEF_VAL))
        c0 = np.float32(random.randint(-10000, 10000))
        capture_param.set_decision_func_params(DecisionFunc.U0, a0, b0, c0)
        capture_param.set_decision_func_params(DecisionFunc.U1, b0, -a0, -c0)
        if do_classification:
            capture_param.sel_dsp_units_to_enable(DspUnit.CLASSIFICATION)

        return capture_param

    def __setup_modules(self, awg_ctrl, cap_ctrl):
        awg_ctrl.initialize(self.__awg)
        cap_ctrl.initialize(*self.__capture_units)
        # キャプチャモジュールをスタートする AWG の設定
        cap_ctrl.select_trigger_awg(self.__capture_module, self.__awg)
        # スタートトリガの有効化
        cap_ctrl.enable_start_trigger(*self.__capture_units)

    def __set_wave_sequence(self, awg_ctrl, do_classification):
        wave_seq = self.__gen_wave_seq(do_classification)
        awg_ctrl.set_wave_sequence(self.__awg, wave_seq)
        return wave_seq

    def __set_capture_params(self, cap_ctrl, wave_seq, do_classification):
        capture_param = self.__gen_capture_param(wave_seq, do_classification)
        for capture_unit in self.__capture_units:
            cap_ctrl.set_capture_params(capture_unit, capture_param)
        return capture_param

    def __get_capture_data(self, cap_ctrl, do_classification):
        capture_unit_to_capture_data = {}
        for capture_unit in self.__capture_units:
            num_samples_to_get = cap_ctrl.num_captured_samples(self.__capture_units[0])
            if do_classification:
                capture_unit_to_capture_data[capture_unit] = cap_ctrl.get_classification_results(capture_unit, num_samples_to_get)
            else:
                capture_unit_to_capture_data[capture_unit] = cap_ctrl.get_capture_data(capture_unit, num_samples_to_get)
        return capture_unit_to_capture_data

    def __calc_expected_capture_data(self, samples, capture_param):
        """キャプチャユニットに samples を入力したときのキャプチャデータを算出する"""
        if DspUnit.CLASSIFICATION in capture_param.dsp_units_enabled:
            i_samples = []
            q_samples = []
            for i_sample, q_sample in samples:
                i_samples.append(fixed_to_float(i_sample, 0))
                q_samples.append(fixed_to_float(q_sample, 0))

            return classification(
                i_samples,
                q_samples,
                capture_param.get_decision_func_params(DecisionFunc.U0),
                capture_param.get_decision_func_params(DecisionFunc.U1))
        
        return [(float(i_data), float(q_data)) for i_data, q_data in samples]

    def __comp_capture_data_to_expected(self, capture_data, expected):
        exp_len = len(expected)
        num_repeats = len(capture_data) // exp_len
        for i in range(exp_len):
            # キャプチャデータは期待値データの繰り返しとなるはず
            # 最初と最後の繰り返しだけ一致するか調べる
            if expected[i] != capture_data[i]:
                return False
            if expected[i] != capture_data[(num_repeats - 1) * exp_len + i]:
                return False
        return True

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

    def run_test(self, do_classification):
        with (self.__create_awg_ctrl() as awg_ctrl,
              self.__create_cap_ctrl() as cap_ctrl):
            # 初期化
            self.__setup_modules(awg_ctrl, cap_ctrl)
            # 波形シーケンスの設定
            wave_seq = self.__set_wave_sequence(awg_ctrl, do_classification)
            # キャプチャパラメータの設定
            capture_param = self.__set_capture_params(cap_ctrl, wave_seq, do_classification)
            # 波形送信スタート
            awg_ctrl.start_awgs(self.__awg)
            # 波形送信完了待ち
            awg_ctrl.wait_for_awgs_to_stop(10, self.__awg)
            # キャプチャ完了待ち
            cap_ctrl.wait_for_capture_units_to_stop(1200, *self.__capture_units)
            # キャプチャデータ取得
            capture_unit_to_capture_data = self.__get_capture_data(cap_ctrl, do_classification)
            # エラーチェック
            awg_errs = awg_ctrl.check_err(self.__awg)
            cap_errs = cap_ctrl.check_err(*self.__capture_units)
            if awg_errs:
                print(awg_errs)
            if cap_errs:
                print(cap_errs)

            # キャプチャサンプル数の確認
            all_match = True
            num_samples_to_capture = capture_param.calc_capture_samples()
            for capture_unit in self.__capture_units:
                if num_samples_to_capture != cap_ctrl.num_captured_samples(capture_unit):
                    all_match = False
                    break

        # AWG の波形データとキャプチャデータを比較
        expected = self.__calc_expected_capture_data(
            wave_seq.chunk(0).wave_data.samples, capture_param)
        for cap_data in capture_unit_to_capture_data.values():
            all_match &= self.__comp_capture_data_to_expected(cap_data, expected)

        # 波形データを保存
        self.__save_wave_samples(expected, capture_unit_to_capture_data)
        self.__save_wave_seq_params(self.__awg, wave_seq)
        self.__save_capture_params(capture_param)

        if awg_errs or cap_errs:
            return False

        return all_match
