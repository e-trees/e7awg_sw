import os
from e7awgsw import AWG, AwgCtrl, WaveSequence, dsp
from e7awgsw import CaptureModule, CaptureCtrl, CaptureParam, DspUnit, CaptureUnit, DecisionFunc
from e7awgsw.labrad import RemoteAwgCtrl, RemoteCaptureCtrl

class CaptureTest(object):

    # テストデザインにおけるキャプチャモジュールと AWG の波形データバスの接続関係
    __CAP_MOD_TO_AWG = {
        CaptureModule.U0 : AWG.U2,
        CaptureModule.U1 : AWG.U15,
        CaptureModule.U2 : AWG.U3,
        CaptureModule.U3 : AWG.U4
    }

    __WAVE_LEN = 16 # words

    def __init__(
        self,
        res_dir,
        ip_addr,
        use_labrad,
        server_ip_addr
    ):
        self.__ip_addr = ip_addr
        self.__server_ip_addr = server_ip_addr
        self.__use_labrad = use_labrad
        self.__res_dir = res_dir
        os.makedirs(self.__res_dir, exist_ok = True)
        self.__awgs = list(self.__CAP_MOD_TO_AWG.values())
        self.__cap_units = CaptureUnit.all()
    
    def __save_capture_samples(self, cap_unit_to_cap_data, dir, filename):
        os.makedirs(dir, exist_ok = True)
        for cap_unit, cap_data_list in cap_unit_to_cap_data.items():
            filepath = dir + '/' + filename + '_{}.txt'.format(cap_unit)
            self.__write_to_file(cap_data_list, filepath)
        
    def __save_capture_params(self, cap_unit_to_cap_param, dir, filename):
        os.makedirs(dir, exist_ok = True)
        for cap_unit, cap_param in cap_unit_to_cap_param.items():
            filepath = dir + '/' + filename + '_{}.txt'.format(cap_unit)
            with open(filepath, 'w') as txt_file:
                txt_file.write(str(cap_param))

    def __write_to_file(self, cap_data_list, filepath):
        with open(filepath, 'w') as txt_file:
            for cap_data in cap_data_list:
                if isinstance(cap_data, tuple):
                    txt_file.write("{}    {}\n".format(cap_data[0], cap_data[1]))
                else:
                    txt_file.write("{}\n".format(cap_data))

    def __output_test_data(
        self,
        test_name,
        cap_unit_to_cap_param,
        cap_unit_to_cap_data,
        cap_unit_to_exp_data):
        dir = self.__res_dir + '/' + test_name
        self.__save_capture_samples(cap_unit_to_cap_data, dir, 'captured')
        self.__save_capture_samples(cap_unit_to_exp_data, dir, 'expected')
        self.__save_capture_params(cap_unit_to_cap_param, dir, 'caprure_params')

    def __gen_wave_seqs(self):
        awg_to_wave_seq = {}
        for awg in AWG.all():
            coef = int(awg) + 1
            num_samples = self.__WAVE_LEN * WaveSequence.NUM_SAMPLES_IN_AWG_WORD
            i_data = [(i + 1) * coef for i in range(num_samples)]
            q_data = [-sample for sample in i_data]
            wave_seq = WaveSequence(
                num_wait_words = 16, # <- キャプチャのタイミングがズレるので変更しないこと.
                num_repeats = 1)
            wave_seq.add_chunk(
                iq_samples = list(zip(i_data, q_data)),
                num_blank_words = 0, 
                num_repeats = 1)
            awg_to_wave_seq[awg] = wave_seq

        return awg_to_wave_seq

    def __gen_capture_params(self):
        cap_unit_to_cap_param = {}
        for cap_unit in self.__cap_units:
            capture_param = CaptureParam()
            capture_param.num_integ_sections = 1
            capture_param.add_sum_section(self.__WAVE_LEN, 1)
            capture_param.real_fir_i_coefs = [int(cap_unit) + 1]
            capture_param.real_fir_q_coefs = [(int(cap_unit) + 1) * 10]
            capture_param.sel_dsp_units_to_enable(DspUnit.REAL_FIR)
            cap_unit_to_cap_param[cap_unit] = capture_param

        return cap_unit_to_cap_param

    def __setup_modules(self, awg_ctrl, cap_ctrl):
        awg_ctrl.initialize(*self.__awgs)
        cap_ctrl.initialize(*self.__cap_units)
        cap_ctrl.disable_start_trigger(*CaptureUnit.all())
        cap_ctrl.enable_start_trigger(*self.__cap_units)

    def __set_wave_sequence(self, awg_ctrl, awg_to_wave_seq):
        for awg, wave_seq in awg_to_wave_seq.items():
            awg_ctrl.set_wave_sequence(awg, wave_seq)

    def __set_capture_params(self, cap_ctrl, cap_unit_to_cap_param):
        for cap_unit, capture_param in cap_unit_to_cap_param.items():
            cap_ctrl.set_capture_params(cap_unit, capture_param)

    def __get_capture_data(self, cap_ctrl):
        cap_unit_to_cap_data = {}
        for cap_unit in self.__cap_units:
            num_cap_samples = cap_ctrl.num_captured_samples(cap_unit)
            cap_unit_to_cap_data[cap_unit] = cap_ctrl.get_capture_data(cap_unit, num_cap_samples)

        return cap_unit_to_cap_data

    def __calc_exp_data(self, cap_mod_to_cap_units, awg_to_wave_seq, cap_unit_to_cap_param):
        cap_unit_to_exp_data = {}
        for cap_mod in CaptureModule.all():
            awg = self.__CAP_MOD_TO_AWG[cap_mod]
            for cap_unit in cap_mod_to_cap_units[cap_mod]:
                samples = awg_to_wave_seq[awg].all_samples(False)
                cap_param = cap_unit_to_cap_param[cap_unit]
                cap_unit_to_exp_data[cap_unit] = dsp(samples, cap_param)

        return cap_unit_to_exp_data
    
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

    def __transfer_wave(self, awg_ctrl, cap_ctrl):
        # 波形送信スタート
        awg_ctrl.start_awgs(*self.__awgs)
        # 波形送信完了待ち
        awg_ctrl.wait_for_awgs_to_stop(10, *self.__awgs)
        # キャプチャ完了待ち
        cap_ctrl.wait_for_capture_units_idle(2400, *self.__cap_units)

    def __to_unit_to_mod(self, mod_to_units):
        unit_to_mod = {unit : None for unit in CaptureUnit.all()}
        for mod, units in mod_to_units.items():
            for unit in units:
                unit_to_mod[unit] = mod

        return unit_to_mod
    
    def __to_trig_to_mods(self, mod_to_trig):
        trig_to_mods = {awg : [] for awg in AWG.all()}
        for mod, trig in mod_to_trig.items():
            trig_to_mods[trig].append(mod)

        return trig_to_mods

    def case_0(self, awg_ctrl, cap_ctrl):
        """
        キャプチャモジュールにキャプチャユニットが割り当てられていないときに, 
        キャプチャモジュールに AWG からスタートトリガを入れてもキャプチャがスタートしないことを確認する.
        """
        cap_ctrl._clear_capture_stop_flags(*self.__cap_units)
        for cap_mod, awg in self.__CAP_MOD_TO_AWG.items():
            cap_ctrl.construct_capture_module(cap_mod)
            cap_ctrl.select_trigger_awg(cap_mod, awg)
        self.__transfer_wave(awg_ctrl, cap_ctrl)

        mod_to_trig_exp = self.__CAP_MOD_TO_AWG
        trig_to_mods_exp = self.__to_trig_to_mods(mod_to_trig_exp)
        cap_mod_to_cap_units_exp = {mod : [] for mod in CaptureModule.all()}
        cap_unit_to_cap_mod_exp = {unit : None for unit in CaptureUnit.all()}

        return all([
            not any(cap_ctrl._get_capture_stop_flags(*self.__cap_units)),
            mod_to_trig_exp == cap_ctrl.get_module_to_trigger(),
            trig_to_mods_exp == cap_ctrl.get_trigger_to_modules(),
            cap_mod_to_cap_units_exp == cap_ctrl.get_module_to_units(),
            cap_unit_to_cap_mod_exp == cap_ctrl.get_unit_to_module()
        ])

    def case_1(self, awg_ctrl, cap_ctrl):
        """
        キャプチャモジュールにスタートトリガが割り当てられていないときに, 
        AWG がスタートトリガをアサートしても, キャプチャがスタートしないことを確認する.
        """
        cap_mod_to_cap_units = {
            CaptureModule.U0 : [CaptureUnit.U0, CaptureUnit.U1, CaptureUnit.U2],
            CaptureModule.U1 : [CaptureUnit.U3, CaptureUnit.U4, CaptureUnit.U5],
            CaptureModule.U2 : [CaptureUnit.U6, CaptureUnit.U7],
            CaptureModule.U3 : [CaptureUnit.U8, CaptureUnit.U9]
        }
        cap_ctrl._clear_capture_stop_flags(*self.__cap_units)
        for cap_mod, cap_units in cap_mod_to_cap_units.items():
            cap_ctrl.construct_capture_module(cap_mod, *cap_units)
            cap_ctrl.select_trigger_awg(cap_mod, None)
        self.__transfer_wave(awg_ctrl, cap_ctrl)

        mod_to_trig_exp = {mod : None for mod in CaptureModule.all()}
        trig_to_mods_exp = {awg : [] for awg in AWG.all()}
        cap_mod_to_cap_units_exp = cap_mod_to_cap_units
        cap_unit_to_cap_mod_exp = self.__to_unit_to_mod(cap_mod_to_cap_units)
        
        return all([
            not any(cap_ctrl._get_capture_stop_flags(*self.__cap_units)),
            mod_to_trig_exp == cap_ctrl.get_module_to_trigger(),
            trig_to_mods_exp == cap_ctrl.get_trigger_to_modules(),
            cap_mod_to_cap_units_exp == cap_ctrl.get_module_to_units(),
            cap_unit_to_cap_mod_exp == cap_ctrl.get_unit_to_module()
        ])
    
    def case_2(self, awg_ctrl, cap_ctrl, awg_to_wave_seq, cap_unit_to_cap_param):
        """
        キャプチャモジュール 1 に全てのキャプチャユニットを割り当てて, 同時にキャプチャできることを確認する.
        """
        cap_mod_to_cap_units = {
            CaptureModule.U0 : [],
            CaptureModule.U1 : self.__cap_units,
            CaptureModule.U2 : [],
            CaptureModule.U3 : []
        }
        cap_ctrl._clear_capture_stop_flags(*self.__cap_units)
        for cap_mod, cap_units in cap_mod_to_cap_units.items():
            cap_ctrl.construct_capture_module(cap_mod, *cap_units)
            cap_ctrl.select_trigger_awg(cap_mod, self.__CAP_MOD_TO_AWG[cap_mod])
        self.__transfer_wave(awg_ctrl, cap_ctrl)
        
        mod_to_trig_exp = self.__CAP_MOD_TO_AWG
        trig_to_mods_exp = self.__to_trig_to_mods(mod_to_trig_exp)
        cap_mod_to_cap_units_exp = cap_mod_to_cap_units
        cap_unit_to_cap_mod_exp = self.__to_unit_to_mod(cap_mod_to_cap_units)

        cap_unit_to_cap_data = self.__get_capture_data(cap_ctrl)
        cap_unit_to_exp_data = self.__calc_exp_data(
            cap_mod_to_cap_units, awg_to_wave_seq, cap_unit_to_cap_param)
        self.__output_test_data(
            'case_2',
            cap_unit_to_cap_param,
            cap_unit_to_cap_data,
            cap_unit_to_exp_data)
        
        return all([
            cap_unit_to_exp_data == cap_unit_to_cap_data,
            mod_to_trig_exp == cap_ctrl.get_module_to_trigger(),
            trig_to_mods_exp == cap_ctrl.get_trigger_to_modules(),
            cap_mod_to_cap_units_exp == cap_ctrl.get_module_to_units(),
            cap_unit_to_cap_mod_exp == cap_ctrl.get_unit_to_module()
        ])

    def case_3(self, awg_ctrl, cap_ctrl, awg_to_wave_seq, cap_unit_to_cap_param):
        """
        キャプチャモジュール 0, 1, 2, 3 に任意のキャプチャユニットを割り当てて, 同時にキャプチャできることを確認する
        """
        cap_mod_to_cap_units = {
            CaptureModule.U0 : [CaptureUnit.U8],
            CaptureModule.U1 : [CaptureUnit.U1, CaptureUnit.U4],
            CaptureModule.U2 : [CaptureUnit.U2, CaptureUnit.U7, CaptureUnit.U9],
            CaptureModule.U3 : [CaptureUnit.U0, CaptureUnit.U3, CaptureUnit.U5, CaptureUnit.U6]
        }
        for cap_mod in CaptureModule.all():
            cap_ctrl.construct_capture_module(cap_mod, *cap_mod_to_cap_units[cap_mod])
            cap_ctrl.select_trigger_awg(cap_mod, self.__CAP_MOD_TO_AWG[cap_mod])
        self.__transfer_wave(awg_ctrl, cap_ctrl)

        mod_to_trig_exp = self.__CAP_MOD_TO_AWG
        trig_to_mods_exp = self.__to_trig_to_mods(mod_to_trig_exp)
        cap_mod_to_cap_units_exp = cap_mod_to_cap_units
        cap_unit_to_cap_mod_exp = self.__to_unit_to_mod(cap_mod_to_cap_units)

        cap_unit_to_cap_data = self.__get_capture_data(cap_ctrl)
        cap_unit_to_exp_data = self.__calc_exp_data(
            cap_mod_to_cap_units, awg_to_wave_seq, cap_unit_to_cap_param)        
        self.__output_test_data(
            'case_3',
            cap_unit_to_cap_param,
            cap_unit_to_cap_data,
            cap_unit_to_exp_data)
        
        return all([
            cap_unit_to_exp_data == cap_unit_to_cap_data,
            mod_to_trig_exp == cap_ctrl.get_module_to_trigger(),
            trig_to_mods_exp == cap_ctrl.get_trigger_to_modules(),
            cap_mod_to_cap_units_exp == cap_ctrl.get_module_to_units(),
            cap_unit_to_cap_mod_exp == cap_ctrl.get_unit_to_module()
        ])

    def run_test(self):
        """
        以下の 4 つの条件を満たすことを確認する.
          1. キャプチャモジュールにキャプチャユニットが割り当てられていないときに,
             キャプチャモジュールに AWG からスタートトリガを入れてもキャプチャがスタートしない.
          2. キャプチャモジュールにスタートトリガが割り当てられていないときに,
             AWG がスタートトリガをアサートしても, キャプチャがスタートしない.
          3. キャプチャモジュール 1 に全てのキャプチャユニットを割り当てて, 期待したデータが同時にキャプチャできる.
          4. キャプチャモジュール 0, 1, 2, 3 に任意のキャプチャユニットを割り当てて, 期待したデータが同時にキャプチャできる.
        """
        with (self.__create_awg_ctrl() as awg_ctrl,
              self.__create_cap_ctrl() as cap_ctrl):
            # 初期化
            self.__setup_modules(awg_ctrl, cap_ctrl)
            # 波形シーケンスの作成
            awg_to_wave_seq = self.__gen_wave_seqs()
            # キャプチャパラメータの作成
            cap_unit_to_cap_param = self.__gen_capture_params()
            # 波形シーケンスの設定
            self.__set_wave_sequence(awg_ctrl, awg_to_wave_seq)
            # キャプチャパラメータの設定
            self.__set_capture_params(cap_ctrl, cap_unit_to_cap_param)
            # 各条件のテスト
            result = [
                self.case_0(awg_ctrl, cap_ctrl),
                self.case_1(awg_ctrl, cap_ctrl),
                self.case_2(awg_ctrl, cap_ctrl, awg_to_wave_seq, cap_unit_to_cap_param),
                self.case_3(awg_ctrl, cap_ctrl, awg_to_wave_seq, cap_unit_to_cap_param)
            ]
            for i in range(len(result)):
                if not result[i]:
                    print('case {} failed'.format(i))
            # エラーチェック
            awg_errs = awg_ctrl.check_err(*self.__awgs)
            cap_errs = cap_ctrl.check_err(*self.__cap_units)
            if awg_errs:
                print(awg_errs)
            if cap_errs:
                print(cap_errs)

        return all(result) and (not awg_errs) and (not cap_errs)
