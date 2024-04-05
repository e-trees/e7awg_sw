import os
import struct
from testutil import gen_random_int_list
from e7awgsw import CaptureModule, AWG, AwgCtrl, CaptureCtrl, WaveSequence, CaptureParam, CaptureUnit
from e7awgsw.labrad import RemoteAwgCtrl, RemoteCaptureCtrl
from e7awgsw.hwparam import WAVE_RAM_PORT, CAPTURE_ADDR
from e7awgsw.udpaccess import WaveRamAccess
from e7awgsw.logger import get_null_logger

class CaptureTest(object):

    # テストデザインにおけるキャプチャモジュールと AWG の接続関係    
    __CAP_MOD_TO_AWG = {
        CaptureModule.U0 : AWG.U2,
        CaptureModule.U1 : AWG.U15 }

    # キャプチャ前にキャプチャデータを格納するメモリに書き込む値
    __MEM_INIT_SAMPLE = (1.0, -1.0)
    
    def __init__(
        self,
        res_dir,
        ip_addr,
        use_labrad,
        server_ip_addr,
        num_cap_units_list):

        self.__ip_addr = ip_addr
        self.__use_labrad = use_labrad
        self.__server_ip_addr = server_ip_addr
        self.__res_dir = res_dir
        self.__cap_units = CaptureModule.get_units(*self.__CAP_MOD_TO_AWG.keys())
        self.__concrete_cap_units = self.__get_concrete_cap_units(num_cap_units_list) # キャプチャモジュール 0, 1 の中に回路として実在するキャプチャユニット
        self.__awg_to_cap_mod = {v : k for k, v in self.__CAP_MOD_TO_AWG.items()}
        os.makedirs(self.__res_dir, exist_ok = True)

    def __get_concrete_cap_units(self, num_cap_units_list):
        cap_units = []
        cap_units_in_cap_mod = [CaptureUnit.U0, CaptureUnit.U1, CaptureUnit.U2, CaptureUnit.U3]
        cap_units.extend(cap_units_in_cap_mod[0:num_cap_units_list[0]])
        cap_units_in_cap_mod = [CaptureUnit.U4, CaptureUnit.U5, CaptureUnit.U6, CaptureUnit.U7]
        cap_units.extend(cap_units_in_cap_mod[0:num_cap_units_list[1]])
        return cap_units

    def __save_wave_samples(self, cap_unit_to_expected, capture_unit_to_capture_data):
        for cap_unit, expected in cap_unit_to_expected.items():
            exp_wave_file = self.__res_dir + '/expected_samples_{}.txt'.format(cap_unit)
            self.__write_to_file(expected, exp_wave_file)

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
            
        for _ in range(2):
            num_samples = WaveSequence.NUM_SAMPLES_IN_WAVE_BLOCK
            i_data = gen_random_int_list(num_samples, -32768, 32767)
            q_data = gen_random_int_list(num_samples, -32768, 32767)
            wave_seq.add_chunk(
                iq_samples = list(zip(i_data, q_data)),
                num_blank_words = 0, 
                num_repeats = 1)

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
        awg_ctrl.initialize(*self.__awg_to_cap_mod.keys())
        cap_ctrl.initialize(*self.__cap_units)
        # キャプチャモジュールをスタートする AWG の設定
        for awg_id, cap_mod in self.__awg_to_cap_mod.items():
            cap_ctrl.select_trigger_awg(cap_mod, awg_id)
        # スタートトリガの有効化
        cap_ctrl.enable_start_trigger(*self.__cap_units)

    def __set_wave_sequence(self, awg_ctrl):
        awg_to_wave_sequence = {}
        for awg_id in self.__awg_to_cap_mod.keys():
            wave_seq = self.__gen_wave_seq()
            awg_to_wave_sequence[awg_id] = wave_seq
            awg_ctrl.set_wave_sequence(awg_id, wave_seq)
        return awg_to_wave_sequence

    def __set_capture_params(self, cap_ctrl, awg_to_wave_sequence):
        cap_unit_to_cap_param = {}
        for awg_id, wave_seq in awg_to_wave_sequence.items():
            capture_param = self.__gen_capture_param(wave_seq)
            capture_units = CaptureModule.get_units(self.__awg_to_cap_mod[awg_id])
            for cap_unit in capture_units:
                cap_ctrl.set_capture_params(cap_unit, capture_param)
                cap_unit_to_cap_param[cap_unit] = capture_param
        return cap_unit_to_cap_param

    def __get_capture_data(self, cap_ctrl, cap_unit_to_cap_param):
        capture_unit_to_capture_data = {}
        for cap_unit in self.__cap_units:
            param = cap_unit_to_cap_param[cap_unit]
            capture_unit_to_capture_data[cap_unit] = \
                cap_ctrl.get_capture_data(cap_unit, param.calc_capture_samples())
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
        
    def __gen_cap_unit_to_expected(self, cap_unit_to_cap_param, awg_to_wave_seq):
        cap_unit_to_expected = {}
        for cap_unit in self.__cap_units:
            if cap_unit in self.__concrete_cap_units:
                awg_id = self.__CAP_MOD_TO_AWG[CaptureUnit.get_module(cap_unit)]
                samples = self.__convert_to_float(awg_to_wave_seq[awg_id].all_samples(False))
            else:
                param = cap_unit_to_cap_param[cap_unit]
                samples = [self.__MEM_INIT_SAMPLE] * param.calc_capture_samples()
            cap_unit_to_expected[cap_unit] = samples
        return cap_unit_to_expected

    def __clear_cap_mem(self):
        wra = WaveRamAccess(self.__ip_addr, WAVE_RAM_PORT, get_null_logger())
        wr_data = struct.pack('<f', self.__MEM_INIT_SAMPLE[0]) \
                + struct.pack('<f', self.__MEM_INIT_SAMPLE[1])
        wr_data *= 1024
        for cap_unit in self.__cap_units:
            wra.write(CAPTURE_ADDR[int(cap_unit)], wr_data)

    def run_test(self):
        """キャプチャモジュール 0 と 1 にキャプチャユニットが過不足なく入っていることを確認する.

        | キャプチャユニット 0 ~ 7 のキャプチャ領域に初期値を書き込んだ後, 
        | FPGA デザイン上に存在しないものも含めてキャプチャ開始を命令する.
        | 存在するキャプチャユニットのキャプチャ領域には AWG から送信したキャプチャデータが書き込まれていることを確認し, 
        | そうでないキャプチャユニットのキャプチャ領域には初期値が書き込まれていることを確認する.

        """
        with (self.__create_awg_ctrl() as awg_ctrl,
              self.__create_cap_ctrl() as cap_ctrl):
            # キャプチャメモリ初期化
            self.__clear_cap_mem()
            # 初期化
            self.__setup_modules(awg_ctrl, cap_ctrl)
            # 波形シーケンスの設定
            awg_to_wave_sequence = self.__set_wave_sequence(awg_ctrl)
            # キャプチャパラメータの設定
            cap_unit_to_cap_param = self.__set_capture_params(cap_ctrl, awg_to_wave_sequence)
            # 波形送信スタート
            awg_ctrl.start_awgs(*self.__awg_to_cap_mod.keys())
            # 波形送信完了待ち
            awg_ctrl.wait_for_awgs_to_stop(10, *self.__awg_to_cap_mod.keys())
            # キャプチャ完了待ち
            cap_ctrl.wait_for_capture_units_idle(60, *self.__cap_units)
            # キャプチャデータ取得
            capture_unit_to_capture_data = self.__get_capture_data(cap_ctrl, cap_unit_to_cap_param)
            # エラーチェック
            awg_errs = awg_ctrl.check_err(*self.__awg_to_cap_mod.keys())
            cap_errs = cap_ctrl.check_err(*self.__cap_units)
            if awg_errs:
                print(awg_errs)
            if cap_errs:
                print(cap_errs)

        cap_unit_to_expected = \
            self.__gen_cap_unit_to_expected(cap_unit_to_cap_param, awg_to_wave_sequence)
        # キャプチャデータと期待値を比較
        all_match = True
        for cap_unit, cap_data in capture_unit_to_capture_data.items():
            expected = cap_unit_to_expected[cap_unit]
            if expected != cap_data:
                all_match = False
        # 波形データを保存
        self.__save_wave_samples(cap_unit_to_expected, capture_unit_to_capture_data)
        for awg_id, wave_seq in awg_to_wave_sequence.items():
            self.__save_wave_seq_params(awg_id, wave_seq)

        if awg_errs or cap_errs:
            return False

        return all_match
