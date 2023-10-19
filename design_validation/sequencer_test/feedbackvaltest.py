import os
import math
import time
import copy
import random
import testutil
from e7awgsw import CaptureUnit, CaptureModule, AWG, WaveSequence, CaptureParam, plot_graph
from e7awgsw import AwgStartCmd, CaptureEndFenceCmd, WaveSequenceSetCmd, CaptureParamSetCmd, CaptureAddrSetCmd, FeedbackCalcOnClassificationCmd
from e7awgsw import AwgStartCmdErr, CaptureEndFenceCmdErr, WaveSequenceSetCmdErr, CaptureParamSetCmdErr, CaptureAddrSetCmdErr, FeedbackCalcOnClassificationCmdErr
from e7awgsw import FeedbackChannel, CaptureParamElem, DspUnit, DecisionFunc
from e7awgsw import AwgCtrl, CaptureCtrl, SequencerCtrl
from e7awgsw import SinWave, IqWave, dsp
from e7awgsw import RemoteAwgCtrl, RemoteCaptureCtrl, RemoteSequencerCtrl
from e7awgsw import MAX_CAPTURE_SIZE, CAPTURE_DATA_ALIGNMENT_SIZE, WAVE_RAM_PORT
from e7awgsw import get_file_logger
from e7awgsw import WaveRamAccess


class FeedbackValTest(object):

    __CAPTURE_ADDR = [
        0x10000000,  0x30000000,  0x50000000,  0x70000000,
        0x90000000,  0xB0000000,  0xD0000000,  0xF0000000,
        0x150000000, 0x170000000]

    def __init__(self, res_dir, awg_cap_ip_addr, seq_ip_addr, server_ip_addr, use_labrad):
        self.__awg_cap_ip_addr = awg_cap_ip_addr
        self.__seq_ip_addr = seq_ip_addr
        self.__server_ip_addr = server_ip_addr
        self.__use_labrad = use_labrad
        self.__res_dir = res_dir
        self.__awgs = [AWG.U2, AWG.U15]
        self.__capture_units = CaptureModule.get_units(CaptureModule.U0, CaptureModule.U1)

        self.__awg_ctrl = self.__create_awg_ctrl()
        self.__cap_ctrl = self.__create_cap_ctrl()
        self.__seq_ctrl = self.__create_seq_ctrl()
        self.__wave_ram_access = WaveRamAccess(awg_cap_ip_addr, WAVE_RAM_PORT, get_file_logger())
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
        self.__cap_ctrl.select_trigger_awg(CaptureModule.U0, self.__awgs[0])
        self.__cap_ctrl.select_trigger_awg(CaptureModule.U1, self.__awgs[1])
        # スタートトリガの有効化
        self.__cap_ctrl.enable_start_trigger(*self.__capture_units)


    def __register_wave_sequences(self, keys, wave_sequences):
        key_to_wave_seq = dict(zip(keys, wave_sequences))
        for awg_id in self.__awgs:
            self.__awg_ctrl.register_wave_sequences(awg_id, key_to_wave_seq)


    def __register_capture_params(self, keys, params):
        for i in range(len(keys)):
            self.__cap_ctrl.register_capture_params(keys[i], params[i])


    def __get_capture_data(self, num_samples, addr_offset, cls_result):
        if cls_result:
            cap_data_getter = self.__cap_ctrl.get_classification_results
        else:
            cap_data_getter = self.__cap_ctrl.get_capture_data

        cap_unit_to_capture_data = {}
        for cap_unit_id in self.__capture_units:
            cap_unit_to_capture_data[cap_unit_id] = cap_data_getter(cap_unit_id, num_samples, addr_offset)

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
        feedback_val_addr,
        elem_offset,
        feedback_channel_id):
        time = 3000 # 24 [us]
        cmds = [
            CaptureAddrSetCmd(1, self.__capture_units, 0),
            FeedbackCalcOnClassificationCmd(2, self.__capture_units, feedback_val_addr, elem_offset),
            # パラメータ更新
            WaveSequenceSetCmd(3, self.__awgs, wave_seq_keys, feedback_channel_id),
            CaptureParamSetCmd(4, self.__capture_units, cap_param_keys, feedback_channel_id),            
            # AWG スタートとキャプチャ停止待ち
            AwgStartCmd(5, self.__awgs, time, wait = True),
            CaptureEndFenceCmd(
                6, self.__capture_units, int(time + 1e3), wait = True, stop_seq = True)
        ]
        return cmds


    def __save_wave_samples(self, capture_unit_to_capture_data, test_name, filename):
        dir = self.__res_dir + '/' + test_name
        os.makedirs(dir, exist_ok = True)
        for cap_unit_id, cap_data_list in capture_unit_to_capture_data.items():
            capture_data_file = dir + '/' + filename + '_{}.txt'.format(cap_unit_id)
            self.__write_to_file(cap_data_list, capture_data_file)


    def __save_capture_params(self, capture_param, test_name, file_suffx):
        dir = self.__res_dir + '/' + test_name
        os.makedirs(dir, exist_ok = True)
        capture_param_file = dir + '/captured_params_{}.txt'.format(file_suffx)
        with open(capture_param_file, 'w') as txt_file:
            txt_file.write(str(capture_param))

    @classmethod
    def __write_to_file(cls, cap_data_list, filepath):
        with open(filepath, 'w') as txt_file:
            for cap_data in cap_data_list:
                if isinstance(cap_data, tuple):
                    txt_file.write("{}    {}\n".format(cap_data[0], cap_data[1]))
                else:
                    txt_file.write("{}\n".format(cap_data))


    def run_test(self, test_name):
        """
        テスト項目
        ・フィードバック値に応じて設定する波形シーケンスとパラメータが適切に切り替わる
        """
        wave_sequences = gen_wave_sequences()
        cap_params = gen_capture_params()
        wave_seq_keys = gen_keys(AwgCtrl.MAX_WAVE_REGISTRY_ENTRIES)
        cap_param_keys = gen_keys(CaptureCtrl.MAX_CAPTURE_PARAM_REGISTRY_ENTRIES)
        # パラメータ登録
        self.__register_wave_sequences(wave_seq_keys, wave_sequences)
        self.__register_capture_params(cap_param_keys, cap_params)
        # フィードバック値書き込み
        fb_val_addr_offset = 128 * 1024 * 1024 + 1
        for cap_addr in self.__CAPTURE_ADDR:
            self.__wave_ram_access.write(
                cap_addr + fb_val_addr_offset, 0xE4.to_bytes(1, 'little'))
        
        success = True
        for feedback_channel_id in self.__capture_units:
            for elem_offset in [0, 1, 2, 3]:
                # コマンド作成
                cmds = self.__gen_cmds(
                    wave_seq_keys,
                    cap_param_keys,
                    fb_val_addr_offset,
                    elem_offset,
                    feedback_channel_id)
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

                wave_sequence = wave_sequences[elem_offset]
                capture_param = cap_params[elem_offset]
                self.__save_capture_params(
                    capture_param, test_name, 'fb_{}_elem_{}'.format(feedback_channel_id, elem_offset))

                # 期待値データ算出
                samples = wave_sequence.all_samples(False)
                expected_data = dsp(samples, capture_param)
                # キャプチャデータ取得
                cap_unit_to_capture_data = \
                    self.__get_capture_data(capture_param.calc_capture_samples(), 0, False)
                # 結果比較
                all_match = True
                for cap_unit, cap_data in cap_unit_to_capture_data.items():
                    if expected_data != cap_data:
                        all_match = False
                        print('fb {}, elem {}, cap_unit {} error'.format(
                            feedback_channel_id, elem_offset, cap_unit))

                # 波形データを保存
                # print('save wave data')
                self.__save_wave_samples(
                    cap_unit_to_capture_data,
                    test_name,
                    'fb_{}_elem_{}_captured'.format(feedback_channel_id, elem_offset))
                self.__save_wave_samples(
                    {'' : expected_data},
                    test_name,
                    'fb_{}_elem_{}_expected'.format(feedback_channel_id, elem_offset))

                if (not all_match) or is_err_detected:
                    success = False
        
        return success


def gen_capture_params():
    params = []
    for i in range(4):
        param = CaptureParam()
        param.num_integ_sections = i + 1
        param.add_sum_section((i + 1) * 32, i + 5)
        params.append(param)
    return params


def gen_random_iq_words(num_words):
    num_samples = WaveSequence.NUM_SAMPLES_IN_AWG_WORD * num_words
    i_data = testutil.gen_random_int_list(num_samples, -32768, 32767)
    q_data = testutil.gen_random_int_list(num_samples, -32768, 32767)
    return list(zip(i_data, q_data))


def gen_wave_sequences():
    wave_sequences = []
    for i in range(4):
        wave_seq = WaveSequence(
            num_wait_words = 32, # <- キャプチャのタイミングがズレるので変更しないこと.
            num_repeats = 1)
        wave_seq.add_chunk(
            iq_samples = gen_random_iq_words(640),
            num_blank_words = 0,
            num_repeats = 1)
        wave_sequences.append(wave_seq)
    return wave_sequences


def gen_keys(max_key):
    tmp = random.randint(0, max_key)
    return [
        tmp,
        (tmp + 10) % (max_key + 1),
        (tmp + 20) % (max_key + 1),
        (tmp + 30) % (max_key + 1)]
