import sys
import os
import pathlib
from testutil import *

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from e7awgsw import *
from e7awgsw.labrad import *
from e7awgsw import hwparam

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
    
    def __save_wave_samples(self, awg_to_expected, capture_unit_to_capture_data):
        for awg_id, expected in awg_to_expected.items():
            udef_wave_file = self.__res_dir + '/user_defined_wave_{}.txt'.format(awg_id)
            self.__write_to_file(expected, udef_wave_file)

        for cap_unit_id, cap_data in capture_unit_to_capture_data.items():
            capture_data_file = self.__res_dir + '/captured_samples_{}.txt'.format(cap_unit_id)
            self.__write_to_file(cap_data, capture_data_file)
        
    def __write_to_file(self, iq_data_list, filepath):
        with open(filepath, 'w') as txt_file:
            for i_data, q_data in iq_data_list:
                txt_file.write("{}    {}\n".format(i_data, q_data))

    def __gen_wave_seq(self):
        wave_seq = WaveSequence(
            num_wait_words = 16, # <- キャプチャのタイミングがズレるので変更しないこと.
            num_repeats = 1)
        
        num_samples = hwparam.MAX_CAPTURE_SIZE // hwparam.CAPTURED_SAMPLE_SIZE # キャプチャ可能な最大サンプル数
        num_repeats = 1024
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

    def __gen_capture_param(self, wave_seq):
        capture_param = CaptureParam()
        capture_param.num_integ_sections = 1
        capture_param.add_sum_section(wave_seq.num_all_words - wave_seq.num_wait_words, 1)
        return capture_param

    def __setup_modules(self, awg_ctrl, cap_ctrl):
        awg_ctrl.initialize(self.__awg)
        cap_ctrl.initialize(*self.__capture_units)
        # キャプチャモジュールをスタートする AWG の設定
        cap_ctrl.select_trigger_awg(self.__capture_module, self.__awg)
        # スタートトリガの有効化
        cap_ctrl.enable_start_trigger(*self.__capture_units)

    def __set_wave_sequence(self, awg_ctrl):
        wave_seq = self.__gen_wave_seq()
        awg_ctrl.set_wave_sequence(self.__awg, wave_seq)
        return wave_seq

    def __set_capture_params(self, cap_ctrl, wave_seq):
        capture_param = self.__gen_capture_param(wave_seq)
        for capture_unit in self.__capture_units:
            cap_ctrl.set_capture_params(capture_unit, capture_param)

    def __get_capture_data(self, cap_ctrl):
        capture_unit_to_capture_data = {}
        for capture_unit_id in self.__capture_units:
            num_captured_samples = cap_ctrl.num_captured_samples(capture_unit_id)
            capture_unit_to_capture_data[capture_unit_id] = cap_ctrl.get_capture_data(
                capture_unit_id, num_captured_samples)
        return capture_unit_to_capture_data

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


    def run_test(self):
        with (self.__create_awg_ctrl() as awg_ctrl,
              self.__create_cap_ctrl() as cap_ctrl):
            # 初期化
            self.__setup_modules(awg_ctrl, cap_ctrl)
            # 波形シーケンスの設定
            wave_seq = self.__set_wave_sequence(awg_ctrl)
            # キャプチャパラメータの設定
            self.__set_capture_params(cap_ctrl, wave_seq)
            # 波形送信スタート
            awg_ctrl.start_awgs(self.__awg)
            # 波形送信完了待ち
            awg_ctrl.wait_for_awgs_to_stop(10, self.__awg)
            # キャプチャ完了待ち
            cap_ctrl.wait_for_capture_units_to_stop(1200, *self.__capture_units)
            # キャプチャデータ取得
            capture_unit_to_capture_data = self.__get_capture_data(cap_ctrl)
            # エラーチェック
            awg_errs = awg_ctrl.check_err(self.__awg)
            cap_errs = cap_ctrl.check_err(*self.__capture_units)
            if awg_errs:
                print(awg_errs)
            if cap_errs:
                print(cap_errs)

        # 送信波形データをキャプチャしたときの期待値データに変換
        expected = self.__convert_to_float(wave_seq.all_samples(False))
        # AWG の波形データとキャプチャデータを比較
        all_match = True
        for cap_data in capture_unit_to_capture_data.values():
            if expected != cap_data:
                all_match = False

        # 波形データを保存
        self.__save_wave_samples({self.__awg: expected}, capture_unit_to_capture_data)
        self.__save_wave_seq_params(self.__awg, wave_seq)

        if awg_errs or cap_errs:
            return False

        return all_match
