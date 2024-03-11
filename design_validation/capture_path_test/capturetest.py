import os
import random
from collections import OrderedDict
from testutil import gen_random_int_list
from e7awgsw import CaptureModule, AWG, AwgCtrl, \
    CaptureUnit, CaptureCtrl, WaveSequence, CaptureParam, DspUnit
from e7awgsw.labrad import RemoteAwgCtrl, RemoteCaptureCtrl

class CaptureTest(object):

    def __init__(self, res_dir, ip_addr, use_labrad, server_ip_addr):
        self.__ip_addr = ip_addr
        self.__use_labrad = use_labrad
        self.__server_ip_addr = server_ip_addr
        self.__res_dir = res_dir
        self.__awg_to_cap_units = OrderedDict([
            (AWG.U2,  CaptureUnit.U2),
            (AWG.U3,  CaptureUnit.U8),
            (AWG.U15, CaptureUnit.U4),
            (AWG.U4,  CaptureUnit.U9)])
        self.__awgs = list(self.__awg_to_cap_units.keys())
        self.__cap_units = list(self.__awg_to_cap_units.values())
        os.makedirs(self.__res_dir, exist_ok = True)
    
    def __save_wave_samples(self, awg_to_expected, *list_of_cap_unit_to_cap_data):
        for awg, expected in awg_to_expected.items():
            udef_wave_file = self.__res_dir + '/user_defined_wave_{}.txt'.format(awg)
            self.__write_to_file(expected, udef_wave_file)

        for i in range(len(list_of_cap_unit_to_cap_data)):
            res_dir = self.__res_dir + '/cap_' + str(i)
            os.makedirs(res_dir, exist_ok = True)
            for cap_unit, cap_data in list_of_cap_unit_to_cap_data[i].items():
                cap_data_file = res_dir + '/captured_samples_{}.txt'.format(cap_unit)
                self.__write_to_file(cap_data, cap_data_file)
        
    def __write_to_file(self, iq_data_list, filepath):
        with open(filepath, 'w') as txt_file:
            for i_data, q_data in iq_data_list:
                txt_file.write("{}    {}\n".format(i_data, q_data))

    def __gen_wave_seq(self):
        wave_seq = WaveSequence(
            num_wait_words = 32, # <- キャプチャのタイミングがズレるので変更しないこと.
            num_repeats = random.randint(1, 4))
            
        num_chunks = random.randint(1, 4)
        for _ in range(num_chunks):
            num_samples = WaveSequence.NUM_SAMPLES_IN_WAVE_BLOCK
            i_data = gen_random_int_list(num_samples, -32768, 32767)
            q_data = gen_random_int_list(num_samples, -32768, 32767)
            wave_seq.add_chunk(
                iq_samples = list(zip(i_data, q_data)),
                num_blank_words = random.randint(0, 16),
                num_repeats = random.randint(1, 4))

        return wave_seq

    def __save_wave_seq_params(self, awg, wave_seq):
        filepath = self.__res_dir + '/wave_seq_params_{}.txt'.format(awg)
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

    def __gen_capture_param(self, wave_seq, enables_dsps):
        capture_param = CaptureParam()
        capture_param.num_integ_sections = 1
        capture_param.add_sum_section(wave_seq.num_all_words - wave_seq.num_wait_words, 1)
        if enables_dsps:
            capture_param.sel_dsp_units_to_enable(*DspUnit.all())
        return capture_param

    def __setup_modules(self, awg_ctrl, cap_ctrl):
        awg_ctrl.initialize(*self.__awgs)
        cap_ctrl.initialize(*self.__cap_units)
        # キャプチャモジュールをスタートする AWG の設定
        for awg, cap_unit in self.__awg_to_cap_units.items():
            cap_ctrl.select_trigger_awg(CaptureUnit.get_module(cap_unit), awg)
        # スタートトリガの有効化
        cap_ctrl.disable_start_trigger(*CaptureUnit.all())
        cap_ctrl.enable_start_trigger(*self.__cap_units)

    def __set_wave_sequence(self, awg_ctrl):
        wave_seq_0 = self.__gen_wave_seq()
        wave_seq_1 = self.__gen_wave_seq()
        awg_to_wave_sequence = {
            self.__awgs[0] : wave_seq_0,
            self.__awgs[1] : wave_seq_0,
            self.__awgs[2] : wave_seq_1,
            self.__awgs[3] : wave_seq_1
        }
        for awg, wave_seq in awg_to_wave_sequence.items():
            awg_ctrl.set_wave_sequence(awg, wave_seq)
        return awg_to_wave_sequence

    def __set_capture_params(self, cap_ctrl, awg_to_wave_sequence, enables_dsps):
        for awg, wave_seq in awg_to_wave_sequence.items():
            cap_unit = self.__awg_to_cap_units[awg]
            capture_param = self.__gen_capture_param(wave_seq, enables_dsps)
            cap_ctrl.set_capture_params(cap_unit, capture_param)

    def __get_capture_data(self, cap_ctrl):
        cap_unit_to_cap_data = {}
        for cap_unit in self.__cap_units:
            num_captured_samples = cap_ctrl.num_captured_samples(cap_unit)
            cap_unit_to_cap_data[cap_unit] = \
                cap_ctrl.get_capture_data(cap_unit, num_captured_samples)
        return cap_unit_to_cap_data

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

    def __run_hardware(self, awg_ctrl, cap_ctrl):
        # 波形送信スタート
        awg_ctrl.start_awgs(*self.__awgs)
        # 波形送信完了待ち
        awg_ctrl.wait_for_awgs_to_stop(10, *self.__awgs)
        # キャプチャ完了待ち
        cap_ctrl.wait_for_capture_units_to_stop(120, *self.__cap_units)
        # キャプチャデータ取得
        cap_unit_to_cap_data = self.__get_capture_data(cap_ctrl)
        # エラーチェック
        awg_errs = awg_ctrl.check_err(*self.__awgs)
        cap_errs = cap_ctrl.check_err(*self.__cap_units)
        if awg_errs:
            print(awg_errs)
        if cap_errs:
            print(cap_errs)
        return cap_unit_to_cap_data, awg_errs, cap_errs

    def __check_capture_data(self, dsp_en, dsp_dis):
        return all([
            # 信号処理機構を無効にしたキャプチャユニットと信号処理が有効で DSP モジュールを全て無効にしたキャプチャユニットの
            # キャプチャデータが一致することを確認する.
            dsp_dis[self.__cap_units[0]] == dsp_en[self.__cap_units[0]],
            dsp_dis[self.__cap_units[2]] == dsp_en[self.__cap_units[2]],
            
            # 信号処理機構を無効にしたキャプチャユニットと信号処理機構を持たないキャプチャユニットの
            # キャプチャデータが一致することを確認する.
            dsp_dis[self.__cap_units[0]] == dsp_en[self.__cap_units[1]],
            dsp_dis[self.__cap_units[1]] == dsp_en[self.__cap_units[0]],
            dsp_dis[self.__cap_units[2]] == dsp_en[self.__cap_units[3]],
            dsp_dis[self.__cap_units[3]] == dsp_en[self.__cap_units[2]]
        ])

    def run_test(self):
        with (self.__create_awg_ctrl() as awg_ctrl,
              self.__create_cap_ctrl() as cap_ctrl):
            # 初期化
            self.__setup_modules(awg_ctrl, cap_ctrl)
            # 波形シーケンスの設定
            awg_to_wave_sequence = self.__set_wave_sequence(awg_ctrl)

            # 信号処理機構を有効化
            cap_ctrl.enable_dsp()
            # キャプチャパラメータの設定.  DSP モジュールは全て無効.
            self.__set_capture_params(cap_ctrl, awg_to_wave_sequence, False)
            # 波形の出力とキャプチャを実行
            cap_unit_to_cap_data_0, awg_errs_0, cap_errs_0 = self.__run_hardware(awg_ctrl, cap_ctrl)

            # 信号処理機構を無効化
            cap_ctrl.disable_dsp()
            # キャプチャパラメータの設定.  信号処理機構が無効化できていることを確認するため, DSP モジュールは全て有効にする.
            self.__set_capture_params(cap_ctrl, awg_to_wave_sequence, True)
            # 波形の出力とキャプチャを実行
            cap_unit_to_cap_data_1, awg_errs_1, cap_errs_1 = self.__run_hardware(awg_ctrl, cap_ctrl)

        # 送信波形データをキャプチャしたときの期待値データに変換
        awg_to_expected = {}
        for awg, wave_seq in awg_to_wave_sequence.items():
            awg_to_expected[awg] = self.__convert_to_float(wave_seq.all_samples(False))

        # 波形データを保存
        self.__save_wave_samples(awg_to_expected, cap_unit_to_cap_data_0, cap_unit_to_cap_data_1)
        for awg, wave_seq in awg_to_wave_sequence.items():
            self.__save_wave_seq_params(awg, wave_seq)

        if awg_errs_0 or cap_errs_0 or \
           awg_errs_1 or cap_errs_1:
            return False

        return self.__check_capture_data(cap_unit_to_cap_data_0, cap_unit_to_cap_data_1)
