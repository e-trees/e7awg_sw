import os
from e7awgsw import CaptureUnit, CaptureModule, AWG, WaveSequence, CaptureParam
from e7awgsw import \
    AwgStartCmd, CaptureEndFenceCmd, WaveSequenceSetCmd, \
    CaptureParamSetCmd, CaptureAddrSetCmd, FeedbackCalcOnClassificationCmd, \
    WaveGenEndFenceCmd, WaveSequenceSelectionCmd, ResponsiveFeedbackCmd, \
    BranchByFlagCmd, AwgStartWithExtTrigAndClsValCmd
from e7awgsw import \
    AwgStartCmdErr, CaptureEndFenceCmdErr, WaveSequenceSetCmdErr, \
    CaptureParamSetCmdErr, CaptureAddrSetCmdErr, FeedbackCalcOnClassificationCmdErr, \
    WaveGenEndFenceCmdErr, BranchByFlagCmdErr, AwgStartWithExtTrigAndClsValCmdErr
from e7awgsw import AwgCtrl, CaptureCtrl, SequencerCtrl, DspUnit
from e7awgsw.labrad import RemoteAwgCtrl, RemoteCaptureCtrl, RemoteSequencerCtrl
from e7awgsw.hwdefs import FourClassifierChannel

class WaitFlagTest(object):

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
        self.__awgs = [AWG.U2, AWG.U3, AWG.U15]
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
        # キャプチャモジュールの構成とスタートトリガを設定
        for cap_mod in CaptureModule.all():
            cap_units = self.__CAP_MOD_TO_UNITS[cap_mod]
            self.__cap_ctrl.construct_capture_module(cap_mod, *cap_units)
            self.__cap_ctrl.select_trigger_awg(cap_mod, AWG.U2)

    def __register_wave_sequences(self, keys, wave_sequences):
        key_to_wave_seq = dict(zip(keys, wave_sequences))
        for awg in self.__awgs:
            self.__awg_ctrl.register_wave_sequences(awg, key_to_wave_seq)


    def __register_capture_params(self, keys, params):
        for i in range(len(keys)):
            self.__cap_ctrl.register_capture_params(keys[i], params[i])


    def __check_err(self):
        awg_to_err = self.__awg_ctrl.check_err(*self.__awgs)
        for awg, err_list in awg_to_err.items():
            print(awg)
            for err in err_list:
                print('    {}'.format(err))
        
        cap_unit_to_err = self.__cap_ctrl.check_err(*self.__capture_units)
        for cap_unit, err_list in cap_unit_to_err.items():
            print('{} err'.format(cap_unit))
            for err in err_list:
                print('    {}'.format(err))

        seq_err_list = self.__seq_ctrl.check_err()
        for seq_err in seq_err_list:
            print(seq_err, '\n')
        
        return bool(awg_to_err or cap_unit_to_err or seq_err_list)


    def exec_cmds(self, cmds):
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
        return not self.__check_err()


    def test_0(self):
        self.__cap_ctrl.disable_start_trigger(*self.__capture_units)
        success = self.exec_cmds(gen_cmds_0())
        reports = self.__seq_ctrl.pop_cmd_err_reports()
        success &= all([
            len(reports) == 1,
            isinstance(reports[0], AwgStartCmdErr),
            reports[0].awg_id_list == [AWG.U15],
            reports[0].cmd_no == 2,
            not reports[0].is_terminated])
        return success


    def test_1(self):
        self.__cap_ctrl.disable_start_trigger(*self.__capture_units)
        success = self.exec_cmds(gen_cmds_1())
        reports = self.__seq_ctrl.pop_cmd_err_reports()
        success &= len(reports) == 0
        return success


    def test_2(self):
        self.__cap_ctrl.enable_start_trigger(*self.__capture_units)
        success = self.exec_cmds(gen_cmds_2())
        reports = self.__seq_ctrl.pop_cmd_err_reports()
        success &= all([
            len(reports) == 2,
            isinstance(reports[0], CaptureEndFenceCmdErr),
            reports[0].capture_unit_id_list == [CaptureUnit.U0, CaptureUnit.U8],
            reports[0].is_in_time,
            reports[0].cmd_no == 10,
            not reports[0].is_terminated,

            isinstance(reports[1], CaptureEndFenceCmdErr),
            not reports[1].capture_unit_id_list,
            not reports[1].is_in_time,
            reports[1].cmd_no == 11,
            not reports[1].is_terminated])
        return success


    def test_3(self):
        self.__cap_ctrl.enable_start_trigger(*self.__capture_units)
        success = self.exec_cmds(gen_cmds_3())
        reports = self.__seq_ctrl.pop_cmd_err_reports()
        success &= all([
            len(reports) == 1,
            isinstance(reports[0], CaptureEndFenceCmdErr),
            reports[0].capture_unit_id_list == [CaptureUnit.U0, CaptureUnit.U8],
            reports[0].is_in_time,
            reports[0].cmd_no == 16,
            not reports[0].is_terminated])
        return success


    def test_4(self):
        self.__cap_ctrl.disable_start_trigger(*self.__capture_units)
        success = self.exec_cmds(gen_cmds_4())
        reports = self.__seq_ctrl.pop_cmd_err_reports()
        success &= all([
            len(reports) == 1,
            isinstance(reports[0], AwgStartCmdErr),
            reports[0].awg_id_list == [AWG.U3, AWG.U15],
            reports[0].cmd_no == 20,
            not reports[0].is_terminated])
        return success


    def test_5(self):
        self.__cap_ctrl.disable_start_trigger(*self.__capture_units)
        success = self.exec_cmds(gen_cmds_5())
        reports = self.__seq_ctrl.pop_cmd_err_reports()
        success &= all([
            len(reports) == 2,
            isinstance(reports[0], WaveGenEndFenceCmdErr),
            reports[0].awg_id_list == [AWG.U3],
            reports[0].is_in_time,
            reports[0].cmd_no == 24,
            not reports[0].is_terminated,

            isinstance(reports[1], WaveGenEndFenceCmdErr),
            not reports[1].awg_id_list,
            not reports[1].is_in_time,
            reports[1].cmd_no == 25,
            not reports[1].is_terminated])
        return success


    def test_6(self):
        self.__cap_ctrl.disable_start_trigger(*self.__capture_units)
        success = self.exec_cmds(gen_cmds_6())
        reports = self.__seq_ctrl.pop_cmd_err_reports()
        success &= all([
            len(reports) == 1,
            isinstance(reports[0], WaveGenEndFenceCmdErr),
            reports[0].awg_id_list == [AWG.U3],
            reports[0].is_in_time,
            reports[0].cmd_no == 29,
            not reports[0].is_terminated])
        return success


    def test_7(self):
        self.__cap_ctrl.enable_start_trigger(*self.__capture_units)
        success = self.exec_cmds(gen_cmds_7())
        reports = self.__seq_ctrl.pop_cmd_err_reports()
        success &= all([
            len(reports) == 2,
            isinstance(reports[0], CaptureEndFenceCmdErr),
            reports[0].capture_unit_id_list == [CaptureUnit.U3],
            reports[0].is_in_time,
            reports[0].cmd_no == 35,
            not reports[0].is_terminated,

            isinstance(reports[1], WaveGenEndFenceCmdErr),
            reports[1].awg_id_list == [AWG.U2],
            reports[1].is_in_time,
            reports[1].cmd_no == 37,
            not reports[1].is_terminated])

        return success


    def test_8(self):
        self.__cap_ctrl.disable_start_trigger(*self.__capture_units)
        success = self.exec_cmds(gen_cmds_8())
        reports = self.__seq_ctrl.pop_cmd_err_reports()
        success &= all([
            len(reports) == 1,
            isinstance(reports[0], BranchByFlagCmdErr),
            reports[0].cmd_counter == -1,
            reports[0].out_of_range_err,
            reports[0].cmd_no == 40,
            not reports[0].is_terminated])
        return success


    def test_9(self):
        self.__cap_ctrl.disable_start_trigger(*self.__capture_units)
        success = self.exec_cmds(gen_cmds_9())
        reports = self.__seq_ctrl.pop_cmd_err_reports()
        success &= all([
            len(reports) == 1,
            isinstance(reports[0], BranchByFlagCmdErr),
            reports[0].cmd_counter == 1025,
            reports[0].out_of_range_err,
            reports[0].cmd_no == 41,
            not reports[0].is_terminated])
        return success


    def test_10(self):
        self.__cap_ctrl.disable_start_trigger(*self.__capture_units)
        success = self.exec_cmds(gen_cmds_10())
        reports = self.__seq_ctrl.pop_cmd_err_reports()
        success &= all([
            len(reports) == 1,
            isinstance(reports[0], AwgStartWithExtTrigAndClsValCmdErr),
            reports[0].awg_id_list == [AWG.U1, AWG.U10],
            reports[0].timeout_err,
            reports[0].cmd_no == 42,
            not reports[0].is_terminated])
        return success


    def run_test(self):
        """
        テスト項目
        ・AWG スタートとキャプチャ終了モニタコマンドの wait フラグが機能する
        ・各種コマンドがエラーになる条件を満たしたときに, 対応するエラーレポートが FPGA から送られる
        """
        wave_seq = [gen_wave_sequence(2048), gen_wave_sequence(1024)]
        cap_params = [
            gen_capture_param(2048, False),
            gen_capture_param(1024, False),
            gen_capture_param(2048, True)]
        # パラメータ登録
        self.__register_wave_sequences([0, 1], wave_seq)
        self.__register_capture_params([0, 1, 2], cap_params)
        return all([
            self.test_0(),
            self.test_1(),
            self.test_2(),
            self.test_3(),
            self.test_4(),
            self.test_5(),
            self.test_6(),
            self.test_7(),
            self.test_8(),
            self.test_9(),
            self.test_10()])


def gen_capture_param(num_sum_section_words, enable_classification):
    param = CaptureParam()
    param.num_integ_sections = 1
    param.add_sum_section(num_sum_section_words, 1)
    if enable_classification:
        param.sel_dsp_units_to_enable(DspUnit.CLASSIFICATION)
    return param


def gen_wave_sequence(num_awg_words):
    wave_seq = WaveSequence(
        num_wait_words = 32,
        num_repeats = 1)
    wave_seq.add_chunk(
        iq_samples = [(1,2)] * num_awg_words * WaveSequence.NUM_SAMPLES_IN_AWG_WORD,
        num_blank_words = 0,
        num_repeats = 1)
    return wave_seq


def gen_cmds_0():
    time = 200 # 1.6 [us]   波形パラメータ設定にかかる最大時間 : 792 [ns], プリロードにかかる最大時間 : 772 [ns]
    cmds = [
        # パラメータ更新  
        WaveSequenceSetCmd(0, [AWG.U3, AWG.U15], key_table = 0),
        # AWG スタート
        AwgStartCmd(1, [AWG.U3],  time,        wait = True),                  # エラーにならないのを期待
        AwgStartCmd(2, [AWG.U15], time + 1024, wait = True, stop_seq = True), # エラーになるのを期待
    ]
    return cmds


def gen_cmds_1():
    time = 200 # 1.6 [us]
    cmds = [
        # パラメータ更新
        WaveSequenceSetCmd(3, [AWG.U3, AWG.U15], key_table = 0),
        # AWG スタート
        AwgStartCmd(4, [AWG.U3],  time,        wait = False),                 # エラーにならないのを期待
        AwgStartCmd(5, [AWG.U15], time + 1024, wait = True, stop_seq = True), # エラーにならないのを期待
    ]
    return cmds


def gen_cmds_2():
    time = 4312 # 34.5 [us]
    cap_unit_set_0 = [CaptureUnit.U0, CaptureUnit.U8]
    cap_unit_set_1 = [CaptureUnit.U1, CaptureUnit.U9]
    cmds = [
        # パラメータ更新
        WaveSequenceSetCmd(6, [AWG.U2, AWG.U15], key_table = 0),
        CaptureParamSetCmd(7, cap_unit_set_0,  key_table = 0),
        CaptureParamSetCmd(8, cap_unit_set_1,  key_table = 1),
        # AWG スタートとキャプチャ停止待ち
        AwgStartCmd(9, [AWG.U2], time, wait = False),                                      # エラーにならないのを期待
        CaptureEndFenceCmd(10, cap_unit_set_0, time + 512,  wait = True),                  # エラーになるのを期待
        CaptureEndFenceCmd(11, cap_unit_set_1, time + 1300, wait = True, stop_seq = True), # エラーになるのを期待
    ]
    return cmds


def gen_cmds_3():
    time = 4312 # 34.5 [us]
    cap_unit_set_0 = [CaptureUnit.U0, CaptureUnit.U8]
    cap_unit_set_1 = [CaptureUnit.U1, CaptureUnit.U9]
    cmds = [
        # パラメータ更新
        WaveSequenceSetCmd(12, [AWG.U2, AWG.U15], key_table = 0),
        CaptureParamSetCmd(13, cap_unit_set_0,  key_table = 0),
        CaptureParamSetCmd(14, cap_unit_set_1,  key_table = 1),
        # AWG スタートとキャプチャ停止待ち
        AwgStartCmd(15, [AWG.U2], time, wait = False),                                     # エラーにならないのを期待
        CaptureEndFenceCmd(16, cap_unit_set_0, time + 512,  wait = False),                 # エラーになるのを期待
        CaptureEndFenceCmd(17, cap_unit_set_1, time + 1300, wait = True, stop_seq = True), # エラーにならないのを期待
    ]
    return cmds


def gen_cmds_4():
    cmds = [
        # パラメータ更新
        WaveSequenceSetCmd(18, [AWG.U3, AWG.U15], key_table = 0),
        # AWG スタート
        AwgStartCmd(19, [AWG.U3, AWG.U15], AwgStartCmd.IMMEDIATE, wait = False),                 # エラーにならないのを期待
        AwgStartCmd(20, [AWG.U3, AWG.U15], AwgStartCmd.IMMEDIATE, wait = True, stop_seq = True), # エラーになるのを期待
    ]
    return cmds


def gen_cmds_5():
    time = 300 # 1280 [ns]
    cmds = [
        # パラメータ更新
        WaveSequenceSetCmd(21, [AWG.U3],  key_table = 0),
        WaveSequenceSetCmd(22, [AWG.U15], key_table = 1),
        # AWG スタートと波形出力完了待ち
        AwgStartCmd(23, [AWG.U3, AWG.U15], time,        wait = False),
        WaveGenEndFenceCmd(24, [AWG.U3],   time + 512,  wait = True),                  # エラーになるのを期待
        WaveGenEndFenceCmd(25, [AWG.U15],  time + 1300, wait = True, stop_seq = True), # エラーになるのを期待
    ]
    return cmds


def gen_cmds_6():
    time = 300 # 2400 [ns]
    cmds = [
        # パラメータ更新
        WaveSequenceSetCmd(26, [AWG.U3],  key_table = 0),
        WaveSequenceSetCmd(27, [AWG.U15], key_table = 1),
        # AWG スタートとキャプチャ停止待ち
        AwgStartCmd(28, [AWG.U3, AWG.U15], time,        wait = False),
        WaveGenEndFenceCmd(29, [AWG.U3],   time + 512,  wait = False),                 # エラーになるのを期待
        WaveGenEndFenceCmd(30, [AWG.U15],  time + 1300, wait = True, stop_seq = True), # エラーにならないのを期待
    ]
    return cmds


def gen_cmds_7():
    #    波形パラメータ設定開始     波形パラメータ設定+プリロード開始    高速FBコマンド終了
    #                  ↓                               ↓         ↓
    # AWG 2          | [  972ns ][==== Wave 0 (8us) ====][ 1196ns ][======== Wave 1 (16us) ========]
    # Capture Unit 3 | ↑        [ 256ns ][======== Capture 0 (17.47us) ========]
    #                | ｜                 [ 952ns ]
    #                  ｜                         ↑
    #            高速FBコマンド開始             四値化結果算出
    
    time = 2250 # 18 [us]
    cmds = [
        # パラメータ更新
        WaveSequenceSelectionCmd(
            31, [AWG.U2], key_table = 0, four_cls_channel_id = FourClassifierChannel.U3),
        WaveSequenceSetCmd(32, [AWG.U2], key_table = 1),
        CaptureParamSetCmd(33, [CaptureUnit.U3], key_table = 2),
        # AWG スタートとキャプチャ停止待ち
        ResponsiveFeedbackCmd(34, [AWG.U2], time, wait = False),
        CaptureEndFenceCmd(35, [CaptureUnit.U3], time + 1375, wait = False),          # エラーになるのを期待 (キャプチャ中)
        CaptureEndFenceCmd(36, [CaptureUnit.U3], time + 2400, wait = False),          # エラーにならないのを期待 (キャプチャ終了後)
        WaveGenEndFenceCmd(37, [AWG.U2],  time + 2500, wait = False),                 # エラーになるのを期待 (2回目の波形出力を実行中)
        WaveGenEndFenceCmd(38, [AWG.U2],  time + 3400, wait = True, stop_seq = True), # エラーにならないのを期待 (2回目の波形出力終了後)
    ]
    return cmds


def gen_cmds_8():
    cmds = [
        WaveSequenceSelectionCmd(39, [AWG.U2], key_table = 0),
        BranchByFlagCmd(40, -2) # 範囲外分岐でエラーになるのを期待
    ]
    return cmds


def gen_cmds_9():
    return [ BranchByFlagCmd(41, 1025) ] # 範囲外分岐でエラーになるのを期待


def gen_cmds_10():
    cmds = [
        AwgStartWithExtTrigAndClsValCmd(
            42, [AWG.U1, AWG.U10], 8000, wait = True, stop_seq = True), # エラーになるのを期待 (タイムアウトフラグが立つ)
    ]
    return cmds
