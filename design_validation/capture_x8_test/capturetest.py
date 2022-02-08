import sys
import os
import random
import pathlib
from testutil import *

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from qubelib import *

class CaptureTest(object):

    IP_ADDR = '10.0.0.16'

    def __init__(self, res_dir):
        self.__res_dir = res_dir
        # テストデザインでは, AWG 2 が Captrue 0, 1, 2, 3 に繋がっており, AWG 15 が Capture 4, 5, 6, 7 に繋がっている
        self.__awg_to_capture_module = {
            AWG.U2  : CaptureModule.U0,
            AWG.U15 : CaptureModule.U1}
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
            num_repeats = random.randint(1, 8))
        
        num_chunks = random.randint(1, 16)
        for _ in range(num_chunks):
            num_samples = random.randint(1, 8) * WaveSequence.NUM_SAMPLES_IN_WAVE_BLOCK
            i_data = gen_random_int_list(num_samples, -32768, 32767)
            q_data = gen_random_int_list(num_samples, -32768, 32767)
            wave_seq.add_chunk(
                iq_samples = list(zip(i_data, q_data)),
                num_blank_words = random.randint(0, 32), 
                num_repeats = random.randint(1, 4))

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
        awg_ctrl.initialize()
        awg_ctrl.enable_awgs(*self.__awg_to_capture_module.keys())
        cap_ctrl.initialize()
        cap_ctrl.enable_capture_units(*CaptureUnit.all())
        # キャプチャモジュールをスタートする AWG の設定
        for awg_id, cap_mod in self.__awg_to_capture_module.items():
            cap_ctrl.select_trigger_awg(cap_mod, awg_id)

    def __set_wave_sequence(self, awg_ctrl):
        awg_to_wave_sequence = {}
        for awg_id in self.__awg_to_capture_module.keys():
            wave_seq = self.__gen_wave_seq()
            awg_to_wave_sequence[awg_id] = wave_seq
            awg_ctrl.set_wave_sequence(awg_id, wave_seq)
        return awg_to_wave_sequence

    def __set_capture_params(self, cap_ctrl, awg_to_wave_sequence):
        for awg_id, wave_seq in awg_to_wave_sequence.items():
            capture_param = self.__gen_capture_param(wave_seq)
            capture_units = CaptureModule.get_units(self.__awg_to_capture_module[awg_id])
            for captu_unit_id in capture_units:
                cap_ctrl.set_capture_params(captu_unit_id, capture_param)

    def __get_capture_data(self, cap_ctrl):
        capture_unit_to_capture_data = {}
        for capture_unit_id in CaptureUnit.all():
            num_captured_samples = cap_ctrl.num_captured_samples(capture_unit_id)
            capture_unit_to_capture_data[capture_unit_id] = cap_ctrl.get_capture_data(capture_unit_id, num_captured_samples)
        return capture_unit_to_capture_data

    def __sort_capture_data_by_awg(self, capture_unit_to_capture_data):
        awg_to_cap_data = {}
        for awg_id, cap_mod in self.__awg_to_capture_module.items():
            cap_units = CaptureModule.get_units(cap_mod)
            cap_unit_to_cap_data = dict(filter(lambda elem: elem[0] in cap_units, capture_unit_to_capture_data.items()))
            awg_to_cap_data[awg_id] = cap_unit_to_cap_data
        return awg_to_cap_data

    def run_test(self):
        awg_ctrl = AwgCtrl(self.IP_ADDR)
        cap_ctrl = CaptureCtrl(self.IP_ADDR)
        # 初期化
        self.__setup_modules(awg_ctrl, cap_ctrl)        
        # 波形シーケンスの設定
        awg_to_wave_sequence = self.__set_wave_sequence(awg_ctrl)
        # キャプチャパラメータの設定
        self.__set_capture_params(cap_ctrl, awg_to_wave_sequence)
        # 波形送信スタート
        awg_ctrl.start_awgs()
        # 波形送信完了待ち
        awg_ctrl.wait_for_awgs_to_stop(5, *self.__awg_to_capture_module.keys())
        # キャプチャ完了待ち
        cap_ctrl.wait_for_capture_units_to_stop(5, *CaptureUnit.all())
        # キャプチャデータ取得
        capture_unit_to_capture_data = self.__get_capture_data(cap_ctrl)

        # 送信波形データをキャプチャしたときの期待値データに変換
        awg_to_expected = {}
        for awg_id, wave_seq in awg_to_wave_sequence.items():
            awg_to_expected[awg_id] = self.__convert_to_float(wave_seq.all_samples(False))

        # キャプチャデータをそれを送った AWG ごとに仕分ける
        awg_to_cap_data = self.__sort_capture_data_by_awg(capture_unit_to_capture_data)
        # AWG の波形データとキャプチャデータを比較
        all_match = True
        for awg_id, expected in awg_to_expected.items():
            for cap_data in awg_to_cap_data[awg_id].values():
                if expected != cap_data:
                    all_match = False
        # 波形データを保存
        self.__save_wave_samples(awg_to_expected, capture_unit_to_capture_data)
        for awg_id, wave_seq in awg_to_wave_sequence.items():
            self.__save_wave_seq_params(awg_id, wave_seq)
        return all_match
