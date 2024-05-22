import os
import testutil
import numpy as np
from e7awgsw import CaptureUnit, CaptureModule, AWG, WaveSequence, CaptureParam
from e7awgsw import \
    AwgStartCmd, CaptureEndFenceCmd, WaveSequenceSetCmd, CaptureParamSetCmd, \
    CaptureAddrSetCmd, FeedbackCalcOnClassificationCmd, WaveSequenceSelectionCmd, \
    ResponsiveFeedbackCmd, FourClassifierChannel
from e7awgsw import AwgCtrl, CaptureCtrl, SequencerCtrl, DspUnit
from e7awgsw.labrad import RemoteAwgCtrl, RemoteCaptureCtrl, RemoteSequencerCtrl

# このサンプル値を四値化した結果をもとに, 高速フィードバック命令の2回目の波形を選択する
SAMPLE_FOR_FOUR_CLS_0 = (2, 1)
SAMPLE_FOR_FOUR_CLS_1 = (-2, -1) 

class ResponsiveFeedbackTest(object):

    # テストデザインにおける AWG とキャプチャモジュールの接続関係
    __AWG_TO_CAP_MOD = {
        AWG.U2 : CaptureModule.U0,
        AWG.U3 : CaptureModule.U2
    }

    # キャプチャモジュールとキャプチャユニットの対応関係
    __CAP_MOD_TO_UNITS = {
        CaptureModule.U0 : [CaptureUnit.U2, CaptureUnit.U8],
        CaptureModule.U2 : [CaptureUnit.U9, CaptureUnit.U7],
    }

    def __init__(self, res_dir, awg_cap_ip_addr, seq_ip_addr, server_ip_addr, use_labrad):
        self.__awg_cap_ip_addr = awg_cap_ip_addr
        self.__seq_ip_addr = seq_ip_addr
        self.__server_ip_addr = server_ip_addr
        self.__use_labrad = use_labrad
        self.__res_dir = res_dir
        self.__awgs = [AWG.U2, AWG.U3]

        # 高速フィードバック処理で使用する四値を算出するキャプチャユニット
        self.__cap_units_with_cls = [
            self.__CAP_MOD_TO_UNITS[CaptureModule.U0][0], # U2
            self.__CAP_MOD_TO_UNITS[CaptureModule.U2][0]  # U9
        ]
        # AWG の出力波形を検証するために使用するキャプチャユニット
        self.__cap_units_plain = [
            self.__CAP_MOD_TO_UNITS[CaptureModule.U0][1], # U8
            self.__CAP_MOD_TO_UNITS[CaptureModule.U2][1]  # U7
        ]
        self.__cap_units = self.__cap_units_with_cls + self.__cap_units_plain
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
        for awg, cap_mod in self.__AWG_TO_CAP_MOD.items():
            self.__cap_ctrl.select_trigger_awg(cap_mod, awg)
        # スタートトリガの有効化
        self.__cap_ctrl.disable_start_trigger(*CaptureUnit.all())
        self.__cap_ctrl.enable_start_trigger(*self.__cap_units)


    def __register_wave_sequences(self, keys, wave_sequences):        
        key_to_wave_seq = dict(zip(keys, wave_sequences))
        for awg in self.__awgs:
            self.__awg_ctrl.register_wave_sequences(awg, key_to_wave_seq)


    def __register_capture_params(self, keys, params):
        for i in range(len(keys)):
            self.__cap_ctrl.register_capture_params(keys[i], params[i])


    def __set_capture_param(self, cap_units, param):
        for cap_unit in cap_units:
            self.__cap_ctrl.set_capture_params(cap_unit, param)


    def __get_capture_data(self, num_samples, cap_units, addr_offset = 0):
        cap_data_list = []
        for cap_unit in cap_units:
            cap_data_list.append(
                self.__cap_ctrl.get_capture_data(cap_unit, num_samples, addr_offset))

        return cap_data_list

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

        seq_err_list = self.__seq_ctrl.check_err()
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


    def __gen_expected_data(
        self,
        first_wave_seq_0,
        second_wave_seqs_0,
        four_cls_val_0,
        first_wave_seq_1,
        second_wave_seqs_1,
        four_cls_val_1):
        exp_data_0 = \
            first_wave_seq_0.all_samples(False) + \
            second_wave_seqs_0[four_cls_val_0].all_samples(False)
        exp_data_1 = \
            first_wave_seq_1.all_samples(False) + \
            second_wave_seqs_1[four_cls_val_1].all_samples(False)
        return [
            list(map(lambda s : (np.float32(s[0]), np.float32(s[1])), exp_data_0)),
            list(map(lambda s : (np.float32(s[0]), np.float32(s[1])), exp_data_1))]


    def __remove_zeros(self, cap_data_list):
        return [
            list(filter(lambda s : s[0] != 0 or s[1] != 0, cap_data))
            for cap_data in cap_data_list]


    def __save_wave_data(
        self, cap_units, cap_data_list, exp_data_list, test_name, test_no):
        cap_unit_to_cap_data = dict(zip(cap_units, cap_data_list))
        cap_unit_to_exp_cap_data = dict(zip(cap_units, exp_data_list))
        self.__save_wave_samples(
            cap_unit_to_cap_data, test_name, 'resp_fb_{}_captured'.format(test_no))
        self.__save_wave_samples(
            cap_unit_to_exp_cap_data, test_name, 'resp_fb_{}_expected'.format(test_no))


    def __save_wave_samples(self, cap_unit_to_cap_data, test_name, filename):
        dir = self.__res_dir + '/' + test_name
        os.makedirs(dir, exist_ok = True)
        for cap_unit, cap_data in cap_unit_to_cap_data.items():
            capture_data_file = dir + '/' + filename + '_{}.txt'.format(cap_unit)
            self.__write_to_file(cap_data, capture_data_file)


    def __save_capture_params(self, capture_param, test_name, filename):
        dir = self.__res_dir + '/' + test_name
        os.makedirs(dir, exist_ok = True)
        capture_param_file = dir + '/' + filename
        with open(capture_param_file, 'w') as txt_file:
            txt_file.write(str(capture_param))


    def __compare_cap_data(self, cap_units, data_0, data_1, test_no):
        all_match = True
        for cap_unit, wave_0, wave_1 in list(zip(cap_units, data_0, data_1)):
            if wave_0 != wave_1:
                all_match = False
                print('resp fb {}, cap_unit {} error'.format(test_no, cap_unit))
        return all_match


    @classmethod
    def __write_to_file(cls, cap_data, filepath):
        with open(filepath, 'w') as txt_file:
            for sample in cap_data:
                if isinstance(sample, tuple):
                    txt_file.write("{}    {}\n".format(sample[0], sample[1]))
                else:
                    txt_file.write("{}\n".format(sample))


    def run_test(self, test_name):
        """
        テスト項目
        ・高速フィードバック処理で AWG に設定する波形シーケンスが, 四値化結果に応じて適切に切り替わる

        高速フィードバック処理で 2 回出力される波形を, 同処理中に 1 回実行されるキャプチャ (DSP は全て無効) でまとめて取得する.
        このとき, [1回目の波形]-[0 データ]-[2回目の波形]-[0データ] という順番で波形がキャプチャされる.
        このキャプチャデータから 0 データを取り除き, [1回目の波形]-[2回目の波形] となったキャプチャデータと
        高速フィードバック処理で AWG から出力される 2 つの波形をつなげたデータが一致するかを確認する.
        """
        # 期待値と比較する波形データを取得するためのキャプチャパラメータを設定
        plain_cap_param = gen_plain_capture_param()
        self.__set_capture_param(self.__cap_units_plain, plain_cap_param)
        # 波形シーケンス作成
        [first_wave_seq_0, *second_wave_seqs_0] = gen_wave_sequences(0)
        [first_wave_seq_1, *second_wave_seqs_1] = gen_wave_sequences(1)
        all_wave_seqs = [first_wave_seq_0] + second_wave_seqs_0 + [first_wave_seq_1] + second_wave_seqs_1
        # 波形レジストリキーを作成
        first_wave_seq_key_0 = 10
        second_wave_seq_keys_0 = [20, 30, 40, 50]
        first_wave_seq_key_1 = 60
        second_wave_seq_keys_1 = [70, 80, 90, 100]
        all_wave_seq_keys = \
            [first_wave_seq_key_0] + second_wave_seq_keys_0 + [first_wave_seq_key_1] + second_wave_seq_keys_1
        # キャプチャパラメータ作成
        cap_params = gen_cls_capture_params()
        # キャプチャパラメータレジストリキーを作成
        cap_param_keys = [100, 200, 300, 400]
        # 波形シーケンスをレジストリに登録
        self.__register_wave_sequences(all_wave_seq_keys, all_wave_seqs)
        # 波形パラメータをレジストリに登録
        self.__register_capture_params(cap_param_keys, cap_params)
        # 四値化結果の期待値
        exp_four_cls_vals_0 = [0, 1, 2, 3]
        exp_four_cls_vals_1 = [3, 2, 1, 0]
        
        success = True
        # 高速フィードバック処理の中で, 二回目の波形が各四値化結果に対応していたか検査する
        for i in range(4):
            # コマンド作成
            cmds = self.__gen_cmds(
                first_wave_seq_key_0, second_wave_seq_keys_0,
                first_wave_seq_key_1, second_wave_seq_keys_1,
                cap_param_keys[i])
            # コマンドを送信
            self.__seq_ctrl.push_commands(cmds)
            # コマンドエラーレポート送信の有効化
            self.__seq_ctrl.enable_cmd_err_report()
            # コマンドの処理をスタート
            self.__seq_ctrl.start_sequencer()
            # コマンドの処理終了待ち
            self.__seq_ctrl.wait_for_sequencer_to_stop(5)
            # コマンドキューをクリア
            self.__seq_ctrl.clear_commands()
            # エラー出力
            is_err_detected = self.__check_err()
            # キャプチャパラメータ保存
            self.__save_capture_params(
                cap_params[i], test_name, 'resp_fb_{}_cap_param.txt'.format(i))
            # 期待値データ算出
            exp_data_list = self.__gen_expected_data(
                first_wave_seq_0, second_wave_seqs_0, exp_four_cls_vals_0[i],
                first_wave_seq_1, second_wave_seqs_1, exp_four_cls_vals_1[i])
            # キャプチャデータ取得
            cap_data_list = self.__get_capture_data(
                plain_cap_param.calc_capture_samples(), self.__cap_units_plain)
            # (I, Q) = (0, 0) を除去
            cap_data_list = self.__remove_zeros(cap_data_list)
            # 結果比較
            all_match = self.__compare_cap_data(
                self.__cap_units_with_cls, exp_data_list, cap_data_list, i)
            # 波形データを保存
            self.__save_wave_data(
                self.__cap_units_with_cls, cap_data_list, exp_data_list, test_name, i)

            if (not all_match) or is_err_detected:
                success = False
        
        return success


def gen_cls_capture_params():
    """
    高速フィードバック処理で使用する四値化結果を算出するためのキャプチャパラメータを生成する.
    """
    params = []
    for i in range(4):
        param = CaptureParam()
        param.num_integ_sections = 1
        param.add_sum_section(16, 1)
        param.sel_dsp_units_to_enable(DspUnit.CLASSIFICATION)
        params.append(param)
    
    # SAMPLE_FOR_FOUR_CLS_0 と params[n] から算出される四値化結果は n になる     (n = 0 ~ 3)
    # SAMPLE_FOR_FOUR_CLS_1 と params[n] から算出される四値化結果は 3 - n になる (n = 0 ~ 3)
    params[0].set_decision_func_params(0, np.float32(1),  np.float32(1),  np.float32(0))
    params[0].set_decision_func_params(1, np.float32(1),  np.float32(-1), np.float32(0))
    params[1].set_decision_func_params(0, np.float32(1),  np.float32(1),  np.float32(0))
    params[1].set_decision_func_params(1, np.float32(-1), np.float32(1),  np.float32(0))
    params[2].set_decision_func_params(0, np.float32(-1), np.float32(-1), np.float32(0))
    params[2].set_decision_func_params(1, np.float32(1),  np.float32(-1), np.float32(0))
    params[3].set_decision_func_params(0, np.float32(-1), np.float32(-1), np.float32(0))
    params[3].set_decision_func_params(1, np.float32(-1), np.float32(1),  np.float32(0))
    return params


def gen_plain_capture_param():
    param = CaptureParam()
    param.num_integ_sections = 1
    param.add_sum_section(340, 1)
    return param


def gen_random_iq_words(num_words):
    num_samples = WaveSequence.NUM_SAMPLES_IN_AWG_WORD * num_words
    i_data = testutil.gen_random_int_list(num_samples, -10000, 10000)
    q_data = testutil.gen_random_int_list(num_samples, -10000, 10000)
    i_data = list(map(lambda x : x * 2 + 1, i_data)) # サンプル値を 0 以外にしたい
    q_data = list(map(lambda x : x * 2 + 1, q_data))
    return list(zip(i_data, q_data))


def gen_wave_sequences(first_sample_sel):
    if first_sample_sel == 0:
        first = SAMPLE_FOR_FOUR_CLS_0
    else:
        first = SAMPLE_FOR_FOUR_CLS_1

    samples_list = [
        [first] + [(0, i + 1) for i in range(63)], # 1 回目の波形
        gen_random_iq_words(16),  # 四値 = 0 のとき出力される 2 回目の波形
        gen_random_iq_words(16),  # 四値 = 1 のとき出力される 2 回目の波形
        gen_random_iq_words(16),  # 四値 = 2 のとき出力される 2 回目の波形
        gen_random_iq_words(16)]  # 四値 = 3 のとき出力される 2 回目の波形
    
    wave_sequences = []
    for samples in samples_list:
        wave_seq = WaveSequence(
            num_wait_words = 32, # <- キャプチャのタイミングがズレるので変更しないこと.
            num_repeats = 1)
        wave_seq.add_chunk(
            iq_samples = samples,
            num_blank_words = 0,
            num_repeats = 1)
        wave_sequences.append(wave_seq)

    return wave_sequences
