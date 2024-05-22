import os
import testutil
import random
import numpy as np
from e7awgsw import CaptureUnit, CaptureModule, AWG, WaveSequence, CaptureParam, plot_graph
from e7awgsw import \
    AwgStartCmd, CaptureEndFenceCmd, WaveSequenceSetCmd, CaptureParamSetCmd, \
    CaptureAddrSetCmd, FeedbackCalcOnClassificationCmd, WaveSequenceSelectionCmd, \
    ResponsiveFeedbackCmd, FourClassifierChannel, BranchByFlagCmd
from e7awgsw import CaptureParamElem, DspUnit, DecisionFunc
from e7awgsw import AwgCtrl, CaptureCtrl, SequencerCtrl
from e7awgsw.labrad import RemoteAwgCtrl, RemoteCaptureCtrl, RemoteSequencerCtrl
from e7awgsw.logger import get_file_logger
from e7awgsw.udpaccess import WaveRamAccess

class BranchTest(object):

    # テストデザインにおけるキャプチャモジュールと AWG の波形データバスの接続関係
    __CAP_MOD_TO_AWG = {
        CaptureModule.U0 : AWG.U2,
        CaptureModule.U1 : AWG.U15,
        CaptureModule.U2 : AWG.U3,
        CaptureModule.U3 : AWG.U4
    }

    # キャプチャモジュールとキャプチャユニットの対応関係
    __CAP_MOD_TO_UNITS = {
        CaptureModule.U0 : [CaptureUnit.U0, CaptureUnit.U1, CaptureUnit.U2, CaptureUnit.U3],
        CaptureModule.U1 : [CaptureUnit.U4, CaptureUnit.U5, CaptureUnit.U6, CaptureUnit.U7],
        CaptureModule.U2 : [CaptureUnit.U8],
        CaptureModule.U3 : [CaptureUnit.U9]
    }

    def __init__(self, res_dir, awg_cap_ip_addr, seq_ip_addr, server_ip_addr, use_labrad):
        self.__awg_cap_ip_addr = awg_cap_ip_addr
        self.__seq_ip_addr = seq_ip_addr
        self.__server_ip_addr = server_ip_addr
        self.__use_labrad = use_labrad
        self.__res_dir = res_dir
        self.__awg_to_cap_unit = {
            AWG.U2 : CaptureUnit.U1,
            AWG.U4 : CaptureUnit.U9
        }
        self.__wave_param_keys = [0, 1]
        self.__awgs = list(self.__awg_to_cap_unit.keys())
        self.__cap_units = list(self.__awg_to_cap_unit.values())
        self.__num_samples = WaveSequence.NUM_SAMPLES_IN_WAVE_BLOCK * 4
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
        self.__cap_ctrl.initialize(*self.__cap_units)
        self.__seq_ctrl.initialize()
        # キャプチャモジュールの構成を設定
        for cap_mod, cap_units in self.__CAP_MOD_TO_UNITS.items():
            self.__cap_ctrl.construct_capture_module(cap_mod, *cap_units)
        # キャプチャモジュールをスタートする AWG の設定
        for cap_mod, awg in self.__CAP_MOD_TO_AWG.items():
            self.__cap_ctrl.select_trigger_awg(cap_mod, awg)
        # スタートトリガの有効化
        self.__cap_ctrl.disable_start_trigger(*CaptureUnit.all())
        self.__cap_ctrl.enable_start_trigger(*self.__cap_units)


    def __gen_wave_seq(self):
        wave_seq = WaveSequence(
            num_wait_words = 32, # <- キャプチャのタイミングがズレるので変更しないこと.
            num_repeats = 1)

        i_data = testutil.gen_random_int_list(self.__num_samples, -32768, 32767)
        q_data = testutil.gen_random_int_list(self.__num_samples, -32768, 32767)
        wave_seq.add_chunk(
            iq_samples = list(zip(i_data, q_data)),
            num_blank_words = 0, 
            num_repeats = 1)
        return wave_seq


    def __register_wave_sequences(self, awg_to_wave_sequences):
        for awg, wave_sequences in awg_to_wave_sequences.items():
            key_to_wave_seq = dict(zip(self.__wave_param_keys, wave_sequences))
            self.__awg_ctrl.register_wave_sequences(awg, key_to_wave_seq)


    def __gen_capture_param(self):
        capture_param = CaptureParam()
        capture_param.num_integ_sections = 1
        num_cap_words = self.__num_samples // CaptureParam.NUM_SAMPLES_IN_ADC_WORD
        capture_param.add_sum_section(num_cap_words, 1)
        return capture_param


    def __set_capture_params(self):
        param = self.__gen_capture_param()
        for cap_unit in self.__cap_units:
            self.__cap_ctrl.set_capture_params(cap_unit, param)


    def __set_cmds(self):
        cmds = [
            BranchByFlagCmd(1, cmd_offset = 3),
            WaveSequenceSetCmd(2, self.__awgs, self.__wave_param_keys[0]),
            AwgStartCmd(3, self.__awgs, AwgStartCmd.IMMEDIATE, wait = True, stop_seq = True),
            WaveSequenceSetCmd(4, self.__awgs, self.__wave_param_keys[1]),
            BranchByFlagCmd(5, cmd_offset = -2),
        ]
        self.__seq_ctrl.push_commands(cmds)


    def __check_err(self):
        awg_to_err = self.__awg_ctrl.check_err(*self.__awgs)
        for awg, err_list in awg_to_err.items():
            print('awg {} err'.format(awg))
            for err in err_list:
                print('    {}'.format(err))
        
        cap_unit_to_err = self.__cap_ctrl.check_err(*self.__cap_units)
        for cap_unit, err_list in cap_unit_to_err.items():
            print('capture unit {} err'.format(cap_unit))
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
        first_wave_seq_key_0,
        second_wave_seq_keys_0,
        first_wave_seq_key_1,
        second_wave_seq_keys_1,
        cap_param_key):
        time = 2500 # 20 [us]
        cls_ch_list = [
            FourClassifierChannel.of(self.__cap_units_with_cls[0]),
            FourClassifierChannel.of(self.__cap_units_with_cls[1])
        ]
        cmds = [
            CaptureAddrSetCmd(1, self.__cap_units, 0),
            CaptureParamSetCmd(2, self.__cap_units_with_cls, cap_param_key),
            WaveSequenceSetCmd(3, self.__awgs[0], first_wave_seq_key_0),
            WaveSequenceSetCmd(4, self.__awgs[1], first_wave_seq_key_1),
            WaveSequenceSelectionCmd(5, self.__awgs[0], second_wave_seq_keys_0, cls_ch_list[0]),
            WaveSequenceSelectionCmd(6, self.__awgs[1], second_wave_seq_keys_1, cls_ch_list[1]),
            ResponsiveFeedbackCmd(7, self.__awgs, time, wait = True, stop_seq = True)
        ]
        return cmds


    @classmethod
    def __gen_expected_data(cls, awg_to_wave_sequences):
        awg_to_exp_data_list = {}
        for awg, wave_seq_list in awg_to_wave_sequences.items():
            converter = lambda s : (np.float32(s[0]), np.float32(s[1]))
            awg_to_exp_data_list[awg] = [
                list(map(converter, wave_seq.all_samples(False)))
                for wave_seq in wave_seq_list
            ]
        return awg_to_exp_data_list


    def __save_wave_data(self, awg_to_cap_data_list, awg_to_exp_data_list, test_name):
        for awg, cap_data_list in awg_to_cap_data_list.items():
            cap_unit = self.__awg_to_cap_unit[awg]
            for i in range(len(cap_data_list)):
                cap_unit_to_cap_data = {cap_unit : cap_data_list[i]}
                self.__save_wave_samples(
                    cap_unit_to_cap_data, test_name, 'wave_{}_captured'.format(i))
        
        for awg, exp_data_list in awg_to_exp_data_list.items():
            cap_unit = self.__awg_to_cap_unit[awg]
            for i in range(len(cap_data_list)):
                cap_unit_to_exp_data = {cap_unit : exp_data_list[i]}
                self.__save_wave_samples(
                    cap_unit_to_exp_data, test_name, 'wave_{}_expected'.format(i))


    def __save_wave_samples(self, cap_unit_to_cap_data, test_name, filename):
        dir = self.__res_dir + '/' + test_name
        os.makedirs(dir, exist_ok = True)
        for cap_unit, cap_data in cap_unit_to_cap_data.items():
            filepath = dir + '/' + filename + '_{}.txt'.format(cap_unit)
            self.__write_to_file(cap_data, filepath)


    @classmethod
    def __write_to_file(cls, cap_data, filepath):
        with open(filepath, 'w') as txt_file:
            for sample in cap_data:
                if isinstance(sample, tuple):
                    txt_file.write("{}    {}\n".format(sample[0], sample[1]))
                else:
                    txt_file.write("{}\n".format(cap_data))


    def run_test(self, test_name):
        """
        テスト項目
        ・分岐フラグにより分岐コマンドの分岐成立/不成立を切り替えられる
        ・分岐成立時に分岐コマンドのパラメータで指定した先のコマンドを実行する
        ・分岐不成立時に分岐コマンドの次のコマンドを実行する
        
        シーケンサコマンドの並びは以下の通り.
        0 - ブランチ          (offset = +3)
        1 - 波形パラメータ設定  (param = 0)
        2 - AWG スタート      (停止フラグ = 1)
        3 - 波形パラメータ設定  (param = 1)
        4 - ブランチ          (offset = -2)

        分岐フラグが偽のとき, コマンドは 0 -> 1 -> 2 の順に実行される.
        分岐フラグが真のとき, コマンドは 0 -> 3 -> 4 -> 2 の順に実行される.
        それぞれの場合においてAWG からは異なる波形が出力されるので, 
        各キャプチャデータが, 対応する波形パラメータの波形と一致するか確認する.
        """
        # 波形シーケンス作成
        awg_to_wave_sequences = {
            awg : [self.__gen_wave_seq(), self.__gen_wave_seq()] for awg in self.__awgs }
        # 波形シーケンス登録
        self.__register_wave_sequences(awg_to_wave_sequences)
        # キャプチャパラメータ設定
        self.__set_capture_params()
        # コマンドエラーレポート送信の有効化
        self.__seq_ctrl.enable_cmd_err_report()
        
        # AWG とそれが出力した波形をキャプチャした結果
        awg_to_cap_data_list = { awg : [] for awg in self.__awgs }
        is_err_detected = False
        for flag in [False, True]:
            # シーケンサコマンド設定
            self.__set_cmds()
            # 分岐を有効化
            self.__seq_ctrl.set_branch_flag(flag)
            # シーケンサコマンド処理開始
            self.__seq_ctrl.start_sequencer()
            # キャプチャ完了待ち
            self.__cap_ctrl.wait_for_capture_units_to_stop(*self.__cap_units)
            # コマンドキューをクリア
            self.__seq_ctrl.clear_commands()
            # エラー出力
            is_err_detected |= self.__check_err()
            # キャプチャデータを取得
            for awg in self.__awgs:
                cap_unit = self.__awg_to_cap_unit[awg]
                cap_data = self.__cap_ctrl.get_capture_data(cap_unit, self.__num_samples, 0)
                awg_to_cap_data_list[awg].append(cap_data)

        # 期待値データ算出
        awg_to_exp_data_list = self.__gen_expected_data(awg_to_wave_sequences)
        # 結果比較
        all_match = awg_to_exp_data_list == awg_to_cap_data_list
        # 波形データを保存
        self.__save_wave_data(awg_to_cap_data_list, awg_to_exp_data_list, test_name)
        success = True
        if (not all_match) or is_err_detected:
            success = False
        
        return success
