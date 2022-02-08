import socket
import time
import struct
from .hwparam import *
from .memorymap import *
from .udpaccess import *
from .hwdefs import *
from .captureparam import *
from .exception import *
from .logger import *

class CaptureCtrl(object):

    # キャプチャモジュールが波形データを保存するアドレス
    __CAPTURE_ADDR = [
        0x10000000,  0x30000000,  0x50000000,  0x70000000,
        0x90000000,  0xB0000000,  0xD0000000,  0xF0000000]
    # キャプチャ RAM のワードサイズ (bytes)
    __CAPTURE_RAM_WORD_SIZE = 32 # bytes
    # 1 キャプチャモジュールが保存可能なサンプル数
    MAX_CAPTURE_SAMPLES = MAX_CAPTURE_SIZE // CAPTURED_SAMPLE_SIZE
    #: キャプチャユニットのサンプリングレート (単位=サンプル数/秒)
    SAMPLING_RATE = 500000000

    def __init__(self, ip_addr, *, enable_lib_log = True, logger = get_null_logger()):
        """
        Args:
            ip_addr (string): キャプチャユニット制御モジュールに割り当てられた IP アドレス (例 '10.0.0.16')
            enable_lib_log (bool):
                | True -> ライブラリの標準のログ機能を有効にする.
                | False -> ライブラリの標準のログ機能を無効にする.
            logger (logging.Logger): ユーザ独自のログ出力に用いる Logger オブジェクト
        """
        self.__loggers = [logger]
        if enable_lib_log:
            self.__loggers.append(get_file_logger())

        try:
            socket.inet_aton(ip_addr)
        except socket.error:
            msg = 'Invalid IP Address {}'.format(ip_addr)
            log_error(msg, *self.__loggers)
            raise ValueError(msg)

        self.__reg_access = CaptureRegAccess(ip_addr, CAPTURE_REG_PORT)
        self.__wave_ram_access = WaveRamAccess(ip_addr, WAVE_RAM_PORT)


    def set_capture_params(self, capture_unit_id, param):
        """引数で指定したキャプチャユニットにキャプチャパラメータを設定する

        Args:
            capture_unit_id (CaptureUnit): キャプチャパラメータを設定するキャプチャユニットの ID 
            param (CaptureParam): 設定するキャプチャパラメータ
        """
        try:
            if not CaptureUnit.includes(capture_unit_id):
                raise ValueError('Invalid capture unit ID  {}'.format(capture_unit_id))
            if not isinstance(param, CaptureParam):
                raise ValueError('Invalid capture param {}'.format(param))
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

        self.__check_capture_size(capture_unit_id, param)
        self.__set_sum_sec_len(capture_unit_id, param.sum_section_list)
        self.__set_num_integ_sectinos(capture_unit_id, param.num_integ_sections)
        self.__enable_dsp_units(capture_unit_id, param.dsp_units_enabled)
        self.__set_capture_delay(capture_unit_id, param.capture_delay)
        self.__set_capture_addr(capture_unit_id)
        self.__set_comp_fir_coefs(capture_unit_id, param.complex_fir_coefs)
        self.__set_real_fir_coefs(capture_unit_id, param.real_fir_i_coefs, param.real_fir_q_coefs)
        self.__set_comp_window_coefs(capture_unit_id, param.complex_window_coefs)
        self.__set_sum_range(capture_unit_id, param.sum_start_word_no, param.num_words_to_sum)


    def __set_sum_sec_len(self, capture_unit_id, sum_sec_list):
        """総和区間長とポストブランク長の設定"""
        base_addr = CaptureParamRegs.Addr.capture(capture_unit_id)
        num_sum_secs = len(sum_sec_list)
        self.__reg_access.write(base_addr, CaptureParamRegs.Offset.NUM_SUM_SECTIONS, num_sum_secs)
        sum_sec_len_list = [sum_sec[0] for sum_sec in sum_sec_list]
        self.__reg_access.multi_write(
            base_addr, CaptureParamRegs.Offset.sum_section_length(0), *sum_sec_len_list)
        post_blank_len_list = [sum_sec[1] for sum_sec in sum_sec_list]
        self.__reg_access.multi_write(
            base_addr, CaptureParamRegs.Offset.post_blank_length(0), *post_blank_len_list)

    def __set_num_integ_sectinos(self, capture_unit_id, num_integ_sectinos):
        """統合区間数の設定"""
        base_addr = CaptureParamRegs.Addr.capture(capture_unit_id)
        self.__reg_access.write(base_addr, CaptureParamRegs.Offset.NUM_INTEG_SECTIONS, num_integ_sectinos)


    def __enable_dsp_units(self, capture_unit_id, dsp_units):
        """DSP ユニットの有効化"""
        reg_val = 0
        for dsp_unit in dsp_units:
            reg_val |= 1 << dsp_unit
        base_addr = CaptureParamRegs.Addr.capture(capture_unit_id)
        self.__reg_access.write(base_addr, CaptureParamRegs.Offset.DSP_MODULE_ENABLE, reg_val)


    def __set_capture_delay(self, capture_unit_id, capture_delay):
        """キャプチャディレイの設定"""
        base_addr = CaptureParamRegs.Addr.capture(capture_unit_id)
        self.__reg_access.write(base_addr, CaptureParamRegs.Offset.CAPTURE_DELAY, capture_delay)


    def __set_capture_addr(self, capture_unit_id):
        """キャプチャアドレスの設定"""
        base_addr = CaptureParamRegs.Addr.capture(capture_unit_id)
        self.__reg_access.write(base_addr, CaptureParamRegs.Offset.CAPTURE_ADDR, self.__CAPTURE_ADDR[capture_unit_id] // 32)


    def __set_comp_fir_coefs(self, capture_unit_id, comp_fir_coefs):
        """複素 FIR フィルタの係数を設定する"""
        base_addr = CaptureParamRegs.Addr.capture(capture_unit_id)
        coef_list = [int(coef.real) for coef in reversed(comp_fir_coefs)]
        self.__reg_access.multi_write(base_addr, CaptureParamRegs.Offset.comp_fir_re_coef(0), *coef_list)
        coef_list = [int(coef.imag) for coef in reversed(comp_fir_coefs)]
        self.__reg_access.multi_write(base_addr, CaptureParamRegs.Offset.comp_fir_im_coef(0), *coef_list)


    def __set_real_fir_coefs(self, capture_unit_id, real_fir_i_coefs, real_fir_q_coefs):
        """実数 FIR フィルタの係数を設定する"""
        base_addr = CaptureParamRegs.Addr.capture(capture_unit_id)
        self.__reg_access.multi_write(
            base_addr, CaptureParamRegs.Offset.real_fir_i_coef(0), *reversed(real_fir_i_coefs))
        self.__reg_access.multi_write(
            base_addr, CaptureParamRegs.Offset.real_fir_q_coef(0), *reversed(real_fir_q_coefs))


    def __set_comp_window_coefs(self, capture_unit_id, complex_window_coefs):
        """複素窓関数の係数を設定する"""
        base_addr = CaptureParamRegs.Addr.capture(capture_unit_id)
        coef_list = [int(coef.real) for coef in complex_window_coefs]
        self.__reg_access.multi_write(base_addr, CaptureParamRegs.Offset.comp_window_re_coef(0), *coef_list)
        coef_list = [int(coef.imag) for coef in complex_window_coefs]
        self.__reg_access.multi_write(base_addr, CaptureParamRegs.Offset.comp_window_im_coef(0), *coef_list)


    def __set_sum_range(self, capture_unit_id, sum_start_word_no, num_words_to_sum):
        """総和区間内の総和範囲を設定する"""
        end_start_word_no = min(sum_start_word_no + num_words_to_sum - 1, CaptureParam.MAX_SUM_SECTION_LEN)
        base_addr = CaptureParamRegs.Addr.capture(capture_unit_id)
        self.__reg_access.write(base_addr, CaptureParamRegs.Offset.SUM_START_TIME, sum_start_word_no)
        self.__reg_access.write(base_addr, CaptureParamRegs.Offset.SUM_END_TIME, end_start_word_no)


    def initialize(self):
        """全てのキャプチャユニットを初期化する"""
        capture_units = CaptureUnit.all()
        self.__reg_access.write(CaptureMasterCtrlRegs.ADDR, CaptureMasterCtrlRegs.Offset.CTRL, 0)
        for capture_unit_id in capture_units:
            self.__reg_access.write(CaptureCtrlRegs.Addr.capture(capture_unit_id), CaptureCtrlRegs.Offset.CTRL, 0)
        self.select_trigger_awg(CaptureModule.U0, None)
        self.select_trigger_awg(CaptureModule.U1, None)
        self.disable_capture_units(*capture_units)
        for cap_unit_id in capture_units:
            self.set_capture_params(cap_unit_id, CaptureParam())
        self.reset_capture_units(*capture_units)


    def get_capture_data(self, capture_unit_id, num_samples):
        """引数で指定したキャプチャユニットが保存したサンプルデータを取得する.
        
        Args:
            capture_unit_id (int): この ID のキャプチャユニットが保存したサンプルデータを取得する
            num_samples (int): 取得するサンプル数 (I と Q はまとめて 1 サンプル)

        Returns:
            sample_list (list of (float, float)): I データと Q データのタプルのリスト.  各データは倍精度浮動小数点数.
        """
        try:
            if not CaptureUnit.includes(capture_unit_id):
                raise ValueError('Invalid capture unit ID {}'.format(capture_unit_id))
            if not isinstance(num_samples, int):
                raise ValueError(
                    "The number of samples must be an integer.  '{}' was set.".format(num_samples))
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

        num_bytes = num_samples * CAPTURED_SAMPLE_SIZE
        num_bytes = (num_bytes + self.__CAPTURE_RAM_WORD_SIZE - 1) // self.__CAPTURE_RAM_WORD_SIZE * self.__CAPTURE_RAM_WORD_SIZE
        rd_data = self.__wave_ram_access.read(self.__CAPTURE_ADDR[capture_unit_id], num_bytes)
        samples = [rd_data[i : i + CAPTURED_SAMPLE_SIZE // 2] for i in range(0, num_bytes, CAPTURED_SAMPLE_SIZE // 2)]
        samples = [struct.unpack('<d', sample)[0] for sample in samples]
        samples = samples[0:num_samples * 2]
        return list(zip(samples[0::2], samples[1::2]))


    def num_captured_samples(self, capture_unit_id):
        """引数で指定したキャプチャユニットが保存したサンプル数を取得する (I データと Q データはまとめて 1 サンプル)

        Returns:
            int: 保存されたサンプル数
        """
        try:
            if not CaptureUnit.includes(capture_unit_id):
                raise ValueError('Invalid capture unit ID {}'.format(capture_unit_id))
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

        base_addr = CaptureParamRegs.Addr.capture(capture_unit_id)
        return self.__reg_access.read(base_addr, CaptureParamRegs.Offset.NUM_CAPTURED_SAMPLES)


    def start_capture_units(self):
        """現在有効になっているキャプチャユニットの処理を開始する"""
        self.__reg_access.write_bits(
            CaptureMasterCtrlRegs.ADDR, CaptureMasterCtrlRegs.Offset.CTRL, CaptureMasterCtrlRegs.Bit.CTRL_START, 1, 1)
        self.__reg_access.write_bits(
            CaptureMasterCtrlRegs.ADDR, CaptureMasterCtrlRegs.Offset.CTRL, CaptureMasterCtrlRegs.Bit.CTRL_START, 1, 0)


    def reset_capture_units(self, *capture_unit_id_list):
        """引数で指定したキャプチャユニットをリセットする

        Args:
            *capture_unit_id_list (list of AWG): リセットするキャプチャユニットの ID
        """
        if not CaptureUnit.includes(*capture_unit_id_list):
            msg = 'Invalid capture unit ID {}'.format(capture_unit_id_list)
            log_error(msg, *self.__loggers)
            raise ValueError(msg)

        for capture_unit_id in capture_unit_id_list:
            self.__reg_access.write_bits(
                CaptureCtrlRegs.Addr.capture(capture_unit_id), CaptureCtrlRegs.Offset.CTRL, CaptureCtrlRegs.Bit.CTRL_RESET, 1, 1)
            time.sleep(10e-6)
            self.__reg_access.write_bits(
                CaptureCtrlRegs.Addr.capture(capture_unit_id), CaptureCtrlRegs.Offset.CTRL, CaptureCtrlRegs.Bit.CTRL_RESET, 1, 0)


    def enable_capture_units(self, *capture_unit_id_list):
        """引数で指定したキャプチャユニットを有効化する

        Args:
            *capture_unit_id_list (list of CaptureUnit): 有効化するキャプチャユニットの ID
        """
        for capture_unit_id in capture_unit_id_list:
            self.__reg_access.write_bits(
                CaptureMasterCtrlRegs.ADDR,
                CaptureMasterCtrlRegs.Offset.ENABLE, 
                CaptureMasterCtrlRegs.Bit.capture(capture_unit_id), 1, 1)


    def disable_capture_units(self, *capture_unit_id_list):
        """引数で指定したキャプチャユニットを無効化する.

        Args:
            *capture_unit_id_list (list of CaptureUnit): 無効化する キャプチャユニット の ID
        """
        for capture_unit_id in capture_unit_id_list:
            self.__reg_access.write_bits(
                CaptureMasterCtrlRegs.ADDR,
                CaptureMasterCtrlRegs.Offset.ENABLE, 
                CaptureMasterCtrlRegs.Bit.capture(capture_unit_id), 1, 0)


    def select_trigger_awg(self, capture_module_id, awg_id):
        """キャプチャモジュールをスタートする AWG を選択する

        Args:
            capture_module_id (CaptureModule): 
                | この ID のキャプチャモジュールに含まれる全キャプチャユニットが, 
                | awg_id で指定した AWG の波形送信開始に合わせてキャプチャを開始する.
            awg_id (AWG or None):
                | capture_module_id で指定したキャプチャモジュールをスタートさせる AWG の ID.
                | None を指定すると, どの AWG もキャプチャモジュールをスタートしなくなる.
        """
        try:
            if not CaptureModule.includes(capture_module_id):
                raise ValueError('Invalid capture module ID {}'.format(capture_module_id))
            if (not AWG.includes(awg_id)) and (awg_id is not None):
                raise ValueError('Invalid AWG ID {}'.format(awg_id))
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

        if capture_module_id == CaptureModule.U0:
            offset = CaptureMasterCtrlRegs.Offset.TRIG_AWG_SEL_0
        elif capture_module_id == CaptureModule.U1:
            offset = CaptureMasterCtrlRegs.Offset.TRIG_AWG_SEL_1
        
        awg_id = 0 if (awg_id is None) else (awg_id + 1)
        self.__reg_access.write(CaptureMasterCtrlRegs.ADDR, offset, awg_id)


    def wait_for_capture_units_to_stop(self, timeout, *capture_unit_id_list):
        """引数で指定した全てのキャプチャユニットの波形の送信が終了するのを待つ

        Args:
            timeout (int or float): タイムアウト値 (単位: 秒). タイムアウトした場合, 例外を発生させる.
            *capture_unit_id_list (list of CaptureUnit): 波形の保存が終了するのを待つキャプチャユニットの ID
        
        Raises:
            CaptureUnitTimeoutError: タイムアウトした場合
        """
        try:
            if (not isinstance(timeout, (int, float))) or (timeout < 0):
                raise ValueError('Invalid timeout {}'.format(timeout))
            if not CaptureUnit.includes(*capture_unit_id_list):
                raise ValueError('Invalid Capture Unit ID {}'.format(capture_unit_id_list))
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

        start = time.time()
        while True:
            all_stopped = True
            for capture_unit_id in capture_unit_id_list:
                val = self.__reg_access.read_bits(
                    CaptureMasterCtrlRegs.ADDR,
                    CaptureMasterCtrlRegs.Offset.DONE_STATUS,
                    CaptureMasterCtrlRegs.Bit.capture(capture_unit_id), 1)
                if val == 0:
                    all_stopped = False
                    break
            if all_stopped:
                return

            elapsed_time = time.time() - start
            if elapsed_time > timeout:
                msg = 'Capture unit stop timeout'
                log_error(msg, *self.__loggers)
                raise CaptureUnitTimeoutError(msg)
            time.sleep(0.01)


    def check_err(self, *capture_unit_id_list):
        """引数で指定したキャプチャユニットのエラーをチェックする.

        エラーのあったキャプチャユニットごとにエラーの種類を返す.

        Args:
            *capture_unit_id_list (CaptureUnit): エラーを調べるキャプチャユニットの ID
        Returns:
            {CaptureUnit -> list of CaptureErr} or None:
            | key = Capture Unit ID
            | value = 発生したエラーのリスト
            | エラーが無かった場合は空の Dict.
        """
        if not CaptureUnit.includes(*capture_unit_id_list):
            msg = 'Invalid Capture Unit ID {}'.format(capture_unit_id_list)
            log_error(msg, *self.__loggers)
            raise ValueError(msg)

        capture_unit_to_err = {}
        for capture_unit_id in capture_unit_id_list:
            err_list = []
            base_addr = CaptureCtrlRegs.Addr.capture(capture_unit_id)
            err = self.__reg_access.read_bits(
                base_addr, CaptureCtrlRegs.Offset.ERR, CaptureCtrlRegs.Bit.ERR_OVERFLOW, 1)
            if err == 1:
                err_list.append(CaptureErr.OVERFLOW)
            err = self.__reg_access.read_bits(
                base_addr, CaptureCtrlRegs.Offset.ERR, CaptureCtrlRegs.Bit.ERR_WRITE, 1)
            if err == 1:
                err_list.append(CaptureErr.MEM_WR)
            if err_list:
                capture_unit_to_err[capture_unit_id] = err_list
        
        return capture_unit_to_err


    def __check_capture_size(self, capture_unit_id, param):
        """キャプチャデータ量が正常かどうか調べる"""
        dsp_units_enabled = param.dsp_units_enabled
        num_cap_samples = param.calc_capture_samples()
        if DspUnit.INTEGRATION in dsp_units_enabled:
            # 積算ユニットが保持できる積算値の数をオーバーしていないかチェック
            if DspUnit.SUM in dsp_units_enabled:
                # 総和が有効な場合, 積算の入力ワードの中に 1 サンプルしか含まれていないので, 
                # 積算ベクトルの要素数 = 1 積算区間当たりのサンプル数となる
                num_integ_vec_elems = num_cap_samples
            else:
                num_integ_vec_elems = num_cap_samples // NUM_SAMPLES_IN_ADC_WORD

            if num_integ_vec_elems > MAX_INTEG_VEC_ELEMS:
                msg = ("The number of elements in the capture unit {}'s integration result vector is too large.  (max = {}, setting = {})"
                       .format(capture_unit_id, MAX_INTEG_VEC_ELEMS, num_integ_vec_elems))
                log_error(msg, *self.__loggers)
                raise ValueError(msg)
        
        elif num_cap_samples > self.MAX_CAPTURE_SAMPLES:
            msg = ('Capture unit {} has too many capture samples.  (max = {}, setting = {})'
                   .format(capture_unit_id, self.MAX_CAPTURE_SAMPLES, num_cap_samples))
            log_error(msg, *self.__loggers)
            raise ValueError(msg)

        if DspUnit.SUM in dsp_units_enabled:
            for sum_sec_no in range(param.num_sum_sections):
                num_words_to_sum = self.__calc_num_words_in_sum_range(sum_sec_no, param)
                if num_words_to_sum > CaptureParam.MAX_SUM_RAMGE_LEN:
                    msg = ('The size of the sum range in sum section {} on capture unit {} is too large.\n'
                           .format(sum_sec_no, capture_unit_id))
                    msg += ('If the number of capture words to be summed exceeds {}, the sum may overflow.  {} was set.\n'
                            .format(CaptureParam.MAX_SUM_RAMGE_LEN, num_words_to_sum))
                    log_warning(msg, *self.__loggers)
                    print('WARNING: ' + msg)

    def __calc_num_words_in_sum_range(self, sum_sec_no, param):
        num_words_in_sum_sec = param.sum_section(sum_sec_no)[0]
        if DspUnit.DECIMATION in param.dsp_units_enabled:
            num_words_in_sum_sec = ((num_words_in_sum_sec + 1) * CaptureParam.NUM_SAMPLES_IN_ADC_WORD) // 32

        sum_end_word_no = min(param.sum_start_word_no + param.num_words_to_sum - 1, num_words_in_sum_sec - 1)
        num_sum_words = sum_end_word_no - max(0, param.sum_start_word_no) + 1
        return max(num_sum_words, 0)
