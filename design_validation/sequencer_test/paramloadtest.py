import sys
import os
import pathlib
import math
import argparse
import time
import copy
import random

lib_path = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.append(lib_path)
from e7awgsw import CaptureUnit, CaptureModule, AWG, WaveSequence, CaptureParam, plot_graph
from e7awgsw import AwgStartCmd, CaptureEndFenceCmd, WaveSequenceSetCmd, CaptureParamSetCmd, CaptureAddrSetCmd, FeedbackCalcOnClassificationCmd
from e7awgsw import AwgStartCmdErr, CaptureEndFenceCmdErr, WaveSequenceSetCmdErr, CaptureParamSetCmdErr, CaptureAddrSetCmdErr, FeedbackCalcOnClassificationCmdErr
from e7awgsw import FeedbackChannel, CaptureParamElem, DspUnit, DecisionFunc
from e7awgsw import AwgCtrl, CaptureCtrl, SequencerCtrl
from e7awgsw import SinWave, IqWave
from e7awgsw.labrad import RemoteAwgCtrl, RemoteCaptureCtrl, RemoteSequencerCtrl
from e7awgsw.hwparam import MAX_CAPTURE_SIZE, CAPTURE_DATA_ALIGNMENT_SIZE
from emulator.dspmodule import dsp

class ParamLoadTest(object):

    # テストデザインにおけるキャプチャモジュールと AWG の接続関係
    __CAP_MOD_TO_AWG = {
        CaptureModule.U0 : AWG.U2,
        CaptureModule.U1 : AWG.U15,
        CaptureModule.U2 : AWG.U3,
        CaptureModule.U3 : AWG.U4
    }

    def __init__(self, res_dir, awg_cap_ip_addr, seq_ip_addr, server_ip_addr, use_labrad):
        self.__awg_cap_ip_addr = awg_cap_ip_addr
        self.__seq_ip_addr = seq_ip_addr
        self.__server_ip_addr = server_ip_addr
        self.__use_labrad = use_labrad
        self.__res_dir = res_dir
        self.__awgs = list(self.__CAP_MOD_TO_AWG.values())
        self.__capture_units = CaptureUnit.all()
        self.__awg_ctrl = self.__create_awg_ctrl()
        self.__cap_ctrl = self.__create_cap_ctrl()
        self.__seq_ctrl = self.__create_seq_ctrl()
        self.__setup_modules()
        os.makedirs(self.__res_dir, exist_ok = True)
    

    def close(self):
        if self.__use_labrad:
            self.__awg_ctrl.disconnect()
            self.__cap_ctrl.disconnect()
            self.__seq_ctrl.disconnect()
        else:
            self.__awg_ctrl.close()
            self.__cap_ctrl.close()
            self.__seq_ctrl.close()


    def __create_awg_ctrl(self):
        if self.__use_labrad:
            return RemoteAwgCtrl(self.__server_ip_addr, self.__awg_cap_ip_addr)
        else:
            return AwgCtrl(self.__awg_cap_ip_addr)


    def __create_cap_ctrl(self):
        if self.__use_labrad:
            return RemoteCaptureCtrl(self.__server_ip_addr, self.__awg_cap_ip_addr)
        else:
            return CaptureCtrl(self.__awg_cap_ip_addr)


    def __create_seq_ctrl(self):
        if self.__use_labrad:
            return RemoteSequencerCtrl(self.__server_ip_addr, self.__seq_ip_addr)
        else:
            return SequencerCtrl(self.__seq_ip_addr)


    def __setup_modules(self):
        self.__awg_ctrl.initialize(*self.__awgs)
        self.__cap_ctrl.initialize(*self.__capture_units)
        self.__seq_ctrl.initialize()
        # キャプチャモジュールをスタートする AWG の設定
        for cap_mod, awg in self.__CAP_MOD_TO_AWG.items():
            self.__cap_ctrl.select_trigger_awg(cap_mod, awg)
        # スタートトリガの有効化
        self.__cap_ctrl.enable_start_trigger(*self.__capture_units)


    def __register_wave_sequences(self, keys, wave_sequences):
        key_to_wave_seq = dict(zip(keys, wave_sequences))
        for awg_id in self.__awgs:
            self.__awg_ctrl.register_wave_sequences(awg_id, key_to_wave_seq)


    def __register_capture_params(self, keys, params):
        for i in range(len(keys)):
            self.__cap_ctrl.register_capture_params(keys[i], params[i])


    def __get_capture_data(self, capture_param, capture_param_none_dsp, addr_offset):
        num_samples = capture_param.calc_capture_samples()
        num_samples_none_dsp = capture_param_none_dsp.calc_capture_samples()
        cls_result = DspUnit.CLASSIFICATION in capture_param.dsp_units_enabled
        cap_unit_to_capture_data = {}

        for cap_unit_id in self.__capture_units:
            if (cap_unit_id == CaptureUnit.U8) or (cap_unit_id == CaptureUnit.U9):
                cap_unit_to_capture_data[cap_unit_id] = \
                    self.__cap_ctrl.get_capture_data(cap_unit_id, num_samples_none_dsp, addr_offset)
            elif cls_result:
                cap_unit_to_capture_data[cap_unit_id] = \
                    self.__cap_ctrl.get_classification_results(cap_unit_id, num_samples, addr_offset)
            else:
                cap_unit_to_capture_data[cap_unit_id] = \
                    self.__cap_ctrl.get_capture_data(cap_unit_id, num_samples, addr_offset)

        return cap_unit_to_capture_data


    def __check_err(self):
        awg_to_err = self.__awg_ctrl.check_err(*self.__awgs)
        for awg_id, err_list in awg_to_err.items():
            print(awg_id)
            for err in err_list:
                print('    {}'.format(err))
        
        cap_unit_to_err = self.__cap_ctrl.check_err(*self.__capture_units)
        for cap_unit_id, err_list in cap_unit_to_err.items():
            print('{} err'.format(cap_unit_id))
            for err in err_list:
                print('    {}'.format(err))

        seq_err_list = self.__cap_ctrl.check_err()
        for seq_err in seq_err_list:
            print(seq_err, '\n')

        cmd_err_reports = self.__seq_ctrl.pop_cmd_err_reports()
        for report in cmd_err_reports:
            print(report, '\n')

        return bool(awg_to_err or cap_unit_to_err or seq_err_list or cmd_err_reports)


    def __gen_cmds(
        self,
        wave_seq_keys,
        cap_param_keys,
        capture_addr_offsets,
        *cap_param_elems):
        param_set_time = 4500 # 36 [us]
        capture_time = int(1e6) # 8 [ms]
        cmds = [
            # 波形シーケンスとキャプチャパラメータの設定            
            WaveSequenceSetCmd(1, self.__awgs, wave_seq_keys[0]),
            CaptureParamSetCmd(2, self.__capture_units, cap_param_keys[0]),
            CaptureAddrSetCmd(3, self.__capture_units, capture_addr_offsets[0]),            

            # キャプチャパラメータ更新 (設定済みのものと合成)
            CaptureParamSetCmd(4, self.__capture_units, cap_param_keys[1], param_elems = cap_param_elems),
            
            # AWG スタートとキャプチャ停止待ち
            AwgStartCmd(5, self.__awgs, param_set_time, wait = True),
            CaptureEndFenceCmd(6, self.__capture_units, param_set_time + capture_time, wait = True),
            
            # 波形シーケンスとキャプチャアドレスの更新
            CaptureAddrSetCmd(7, self.__capture_units, capture_addr_offsets[1]),
            WaveSequenceSetCmd(8, self.__awgs, wave_seq_keys[1]),

            # AWG スタートとキャプチャ停止待ち
            AwgStartCmd(9, self.__awgs, 2 * param_set_time + capture_time, wait = True),
            CaptureEndFenceCmd(
                10, self.__capture_units, 2 * (param_set_time + capture_time), wait = True, stop_seq = True)
        ]
        return cmds


    def __save_wave_samples(self, capture_unit_to_capture_data, test_name, filename):
        dir = self.__res_dir + '/' + test_name
        os.makedirs(dir, exist_ok = True)
        for cap_unit_id, cap_data_list in capture_unit_to_capture_data.items():
            capture_data_file = dir + '/' + filename + '_{}.txt'.format(cap_unit_id)
            ParamLoadTest.__write_to_file(cap_data_list, capture_data_file)


    def __save_capture_params(self, capture_param, dirname, filename):
        dir = self.__res_dir + '/' + dirname
        os.makedirs(dir, exist_ok = True)
        capture_param_file = dir + '/' + filename
        with open(capture_param_file, 'w') as txt_file:
            txt_file.write(str(capture_param))


    def __compare_capture_data(
        self, wave_no, cap_unit_to_capture_data, expected_data, expected_data_none_dsp):
        all_match = True
        for cap_unit, cap_data in cap_unit_to_capture_data.items():
            if (cap_unit == CaptureUnit.U8) or (cap_unit == CaptureUnit.U9):
                if expected_data_none_dsp != cap_data:
                    all_match = False
                    print('wave {}, cap_unit {} error'.format(wave_no, cap_unit))
            else:
                if expected_data != cap_data:
                    all_match = False
                    print('wave {}, cap_unit {} error'.format(wave_no, cap_unit))
        
        return all_match


    def __gen_complex_capture_params(
        self, test_name, cap_param_base, cap_param_diff, *cap_param_elems):
        # キャプチャユニット 0 ~ 7 のキャプチャに使われた合成キャプチャパラメータを作成
        capture_param = combine_capture_params(cap_param_base, cap_param_diff, *cap_param_elems)
        # キャプチャユニット 8, 9 のキャプチャに使われた合成キャプチャパラメータを作成
        capture_param_none_dsp = combine_capture_params(
            capture_param, CaptureParam(), CaptureParamElem.DSP_UNITS)

        self.__save_capture_params(capture_param, test_name, 'captured_params.txt')
        self.__save_capture_params(
            capture_param_none_dsp, test_name, 'captured_params_none_dsp.txt')
        return capture_param, capture_param_none_dsp


    @classmethod
    def __write_to_file(cls, cap_data_list, filepath):
        with open(filepath, 'w') as txt_file:
            for cap_data in cap_data_list:
                if isinstance(cap_data, tuple):
                    txt_file.write("{}    {}\n".format(cap_data[0], cap_data[1]))
                else:
                    txt_file.write("{}\n".format(cap_data))

    def run_test(
        self,
        test_name,
        wave_seq_0,
        wave_seq_1,
        cap_param_base,
        cap_param_diff,
        *cap_param_elems):
        """
        テスト項目
        ・シーケンサコマンドで, キャプチャパラメータの一部の要素のみをセットできる
        ・シーケンサコマンドで, 波形シーケンスがセットできる
        ・シーケンサコマンドで, キャプチャパラメータをセットできる
        ・シーケンサコマンドで, AWG をスタートできる
        ・シーケンサコマンドで, キャプチャの完了をチェックできる

        キャプチャパラメータ (cap_param_base) をセットしてから, 別のキャプチャパラメータ (cap_param_diff) の 
        cap_param_elems の要素だけセットして, 波形シーケンス (wave_seq_0, wave_seq_1 ) の送信とキャプチャを行う.
        2 つのキャプチャパラメータを組み合わせたパラメータによるキャプチャ結果が期待値と一致するかチェックする.
        """
        wave_seq_keys = gen_keys(AwgCtrl.MAX_WAVE_REGISTRY_ENTRIES)
        cap_param_keys = gen_keys(CaptureCtrl.MAX_CAPTURE_PARAM_REGISTRY_ENTRIES)
        capture_addr_offsets = gen_capture_addr_offsets()
        wave_sequences = [wave_seq_0, wave_seq_1]
        
        # パラメータ登録
        self.__register_wave_sequences(wave_seq_keys, wave_sequences)
        self.__register_capture_params(
            cap_param_keys, [cap_param_base, cap_param_diff])
        # コマンド作成
        cmds = self.__gen_cmds(wave_seq_keys, cap_param_keys, capture_addr_offsets, *cap_param_elems)
        # コマンドを送信
        self.__seq_ctrl.push_commands(cmds)
        # コマンドエラーレポート送信の有効化
        self.__seq_ctrl.enable_cmd_err_report()
        # コマンドの処理をスタート
        self.__seq_ctrl.start_sequencer()
        # コマンドの処理終了待ち
        self.__seq_ctrl.wait_for_sequencer_to_stop(5)
        # エラー出力
        is_err_detected = self.__check_err()
        # キャプチャに使われるキャプチャパラメータを作成
        capture_param, capture_param_none_dsp = self.__gen_complex_capture_params(
            test_name, cap_param_base, cap_param_diff, *cap_param_elems)

        for i in range(len(wave_sequences)):
            # 期待値データ算出
            samples = wave_sequences[i].all_samples(False)
            expected_data = dsp(samples, capture_param)
            expected_data_none_dsp = dsp(samples, capture_param_none_dsp)
            # キャプチャデータ取得
            cap_unit_to_capture_data = self.__get_capture_data(
                capture_param, capture_param_none_dsp, capture_addr_offsets[i])
            # 結果比較
            all_match = self.__compare_capture_data(
                i, cap_unit_to_capture_data, expected_data, expected_data_none_dsp)
            # 波形データを保存
            # print('save wave data')
            self.__save_wave_samples(
                cap_unit_to_capture_data, test_name, 'wave_{}_captured'.format(i))
            self.__save_wave_samples(
                {'' : expected_data}, test_name, 'wave_{}_expected_dsp'.format(i))
            self.__save_wave_samples(
                {'' : expected_data_none_dsp}, test_name, 'wave_{}_expected_none_dsp'.format(i))
        
        return all_match and (not is_err_detected)


def combine_capture_params(base, diff, *elems):
    cap_param = copy.copy(base)
    if CaptureParamElem.DSP_UNITS in elems:
        cap_param.sel_dsp_units_to_enable(*diff.dsp_units_enabled)
        
    if CaptureParamElem.CAPTURE_DELAY in elems:
        cap_param.capture_delay = diff.capture_delay

    if CaptureParamElem.NUM_INTEG_SECTIONS in elems:
        cap_param.num_integ_sections = diff.num_integ_sections

    # 総和区間数だけ -> diff の方が短ければ OK
    if ((CaptureParamElem.NUM_SUM_SECTIONS     in elems) and
        (CaptureParamElem.SUM_SECTION_LEN  not in elems) and 
        (CaptureParamElem.POST_BLANK_LEN   not in elems)):
        if base.num_sum_sections < diff.num_sum_sections:
            raise ValueError(
                'The number of sum sections in the base capture param is smaller than that in the diff capture param.')
        base_sum_sections = base.sum_section_list
        diff_sum_sections = diff.sum_section_list
        cap_param.clear_sum_sections()
        for i in range(len(diff_sum_sections)):
            cap_param.add_sum_section(base_sum_sections[i][0], base_sum_sections[i][1])

    # 総和区間長だけ -> diff の方が長ければ OK
    if ((CaptureParamElem.NUM_SUM_SECTIONS not in elems) and
        (CaptureParamElem.SUM_SECTION_LEN      in elems) and 
        (CaptureParamElem.POST_BLANK_LEN   not in elems)):
        if base.num_sum_sections > diff.num_sum_sections:
            raise ValueError(
                'The number of sum sections in the base capture param is bigger than that in the diff capture param.')
        base_sum_sections = base.sum_section_list
        diff_sum_sections = diff.sum_section_list
        cap_param.clear_sum_sections()
        for i in range(len(base_sum_sections)):
            cap_param.add_sum_section(diff_sum_sections[i][0], base_sum_sections[i][1])

    # ポストブランク長だけ -> diff の方が長ければ OK
    if ((CaptureParamElem.NUM_SUM_SECTIONS not in elems) and
        (CaptureParamElem.SUM_SECTION_LEN  not in elems) and 
        (CaptureParamElem.POST_BLANK_LEN       in elems)):
        if base.num_sum_sections > diff.num_sum_sections:
            raise ValueError(
                'The number of sum sections in the base capture param is bigger than that in the diff capture param.')
        base_sum_sections = base.sum_section_list
        diff_sum_sections = diff.sum_section_list
        cap_param.clear_sum_sections()
        for i in range(len(base_sum_sections)):
            cap_param.add_sum_section(base_sum_sections[i][0], diff_sum_sections[i][1])

    # 総和区間長とポストブランク長だけ -> diff の方が長ければ OK
    if ((CaptureParamElem.NUM_SUM_SECTIONS not in elems) and
        (CaptureParamElem.SUM_SECTION_LEN      in elems) and 
        (CaptureParamElem.POST_BLANK_LEN       in elems)):
        if base.num_sum_sections > diff.num_sum_sections:
            raise ValueError(
                'The number of sum sections in the base capture param is bigger than that in the diff capture param.')
        base_sum_sections = base.sum_section_list
        diff_sum_sections = diff.sum_section_list
        cap_param.clear_sum_sections()
        for i in range(len(base_sum_sections)):
            cap_param.add_sum_section(diff_sum_sections[i][0], diff_sum_sections[i][1])

    # 総和区間数と総和区間長だけ -> diff の方が短ければ OK
    if ((CaptureParamElem.NUM_SUM_SECTIONS     in elems) and
        (CaptureParamElem.SUM_SECTION_LEN      in elems) and 
        (CaptureParamElem.POST_BLANK_LEN   not in elems)):
        if base.num_sum_sections < diff.num_sum_sections:
            raise ValueError(
                'The number of sum sections in the base capture param is smaller than that in the diff capture param.')
        base_sum_sections = base.sum_section_list
        diff_sum_sections = diff.sum_section_list
        cap_param.clear_sum_sections()
        for i in range(len(diff_sum_sections)):
            cap_param.add_sum_section(diff_sum_sections[i][0], base_sum_sections[i][1])

    # 総和区間数とポストブランク長だけ -> diff の方が短ければ OK
    if ((CaptureParamElem.NUM_SUM_SECTIONS     in elems) and
        (CaptureParamElem.SUM_SECTION_LEN  not in elems) and 
        (CaptureParamElem.POST_BLANK_LEN       in elems)):
        if base.num_sum_sections < diff.num_sum_sections:
            raise ValueError(
                'The number of sum sections in the base capture param is smaller than that in the diff capture param.')
        base_sum_sections = base.sum_section_list
        diff_sum_sections = diff.sum_section_list
        cap_param.clear_sum_sections()
        for i in range(len(diff_sum_sections)):
            cap_param.add_sum_section(base_sum_sections[i][0], diff_sum_sections[i][1])

    if ((CaptureParamElem.NUM_SUM_SECTIONS in elems) and
        (CaptureParamElem.SUM_SECTION_LEN  in elems) and 
        (CaptureParamElem.POST_BLANK_LEN   in elems)):
        cap_param.clear_sum_sections()
        for num_words, num_post_blank_words in diff.sum_section_list:
            cap_param.add_sum_section(num_words, num_post_blank_words)

    if CaptureParamElem.SUM_TARGET_INTERVAL in elems:
        cap_param.sum_start_word_no = diff.sum_start_word_no
        cap_param.num_words_to_sum = diff.num_words_to_sum

    if CaptureParamElem.COMP_FIR_COEF in elems:
        cap_param.complex_fir_coefs = diff.complex_fir_coefs

    if CaptureParamElem.REAL_FIR_COEF in elems:
        cap_param.real_fir_i_coefs = diff.real_fir_i_coefs
        cap_param.real_fir_q_coefs = diff.real_fir_q_coefs

    if CaptureParamElem.COMP_WINDOW_COEF in elems:
        cap_param.complex_window_coefs = diff.complex_window_coefs

    if CaptureParamElem.DICISION_FUNC_PARAM in elems:
        for func_sel in DecisionFunc.all():
            coef_a, coef_b, const_c = diff.get_decision_func_params(func_sel)
            cap_param.set_decision_func_params(func_sel, coef_a, coef_b, const_c)
    
    return cap_param


def gen_keys(max_key):
    tmp = random.randint(0, max_key)
    return [tmp, (tmp + 10) % (max_key + 1)]


def gen_capture_addr_offsets():
    max_addr_offset = MAX_CAPTURE_SIZE // 2
    tmp = (random.randint(
        0, (max_addr_offset // CAPTURE_DATA_ALIGNMENT_SIZE)) * CAPTURE_DATA_ALIGNMENT_SIZE)
    return [tmp, tmp + 32 * 1024 * 1024]
