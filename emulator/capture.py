import sys
import threading
import pathlib
import struct
import dspmodule
from concurrent.futures import ThreadPoolExecutor
from enum import IntEnum

lib_path = str(pathlib.Path(__file__).resolve().parents[1])
sys.path.append(lib_path)
from e7awgsw import *
from e7awgsw.memorymap import *
from e7awgsw.hwparam import *
from e7awgsw.logger import *


class CaptureUnit(object):

    PARAM_REG_SIZE = 4 # bytes
    __NUM_PARAM_REGS = 16384
    __MAX_PARAM_REG_ADDR = __NUM_PARAM_REGS * PARAM_REG_SIZE
    # シミュレータが受付可能なキャプチャ区間の最大サンプル数.  保存可能なサンプル数ではない点に注意.
    __MAX_SAMPLES_IN_CAPTURE_SECTION = 32 * 1024 * 1024 + 4 

    def __init__(self, id, mem_writer, capture_start_delay):
        self.__state = CaptureUnitState.IDLE
        self.__state_lock = threading.RLock()
        self.__param_regs = [0] * self.__NUM_PARAM_REGS
        self.__mem_writer = mem_writer
        self.__capture_start_delay = capture_start_delay # キャプチャスタートからキャプチャディレイをカウントし始めるまでの準備時間 (単位 : ワード)
        self.__id = id
        self.__executor = ThreadPoolExecutor(max_workers = 2)
        self.__loggers = [get_file_logger(), get_stderr_logger()]
        self.__set_default_params()

    @property
    def id(self):
        return self.__id


    def assert_reset(self):
        """キャプチャユニットをリセット状態にする"""
        with self.__state_lock:
            self.__state = CaptureUnitState.RESET


    def diassert_reset(self):
        """キャプチャユニットのリセットを解除する"""
        with self.__state_lock:
            if self.__state == CaptureUnitState.RESET:
                self.__state = CaptureUnitState.IDLE


    def terminate(self):
        """キャプチャユニットを強制停止する"""
        with self.__state_lock:
            if self.__state == CaptureUnitState.CAPTURE_WAVE:
                self.__state = CaptureUnitState.COMPLETE


    def capture_wave(self, wave_data, *, is_async = False):
        """波形をキャプチャする"""
        with self.__state_lock:
            if (self.__state != CaptureUnitState.IDLE) and (self.__state != CaptureUnitState.COMPLETE):
                return
            self.__state = CaptureUnitState.CAPTURE_WAVE
        
        if is_async:
            self.__executor.submit(self.__capture_wave, wave_data)
        else:
            self.__capture_wave(wave_data)


    def __capture_wave(self, wave_data):
        try:
            capture_param = self.__gen_capture_param()
            self.__check_capture_size(capture_param)
            num_samples_to_waste = self.__calc_num_samples_to_waste(capture_param.capture_delay)
            samples = wave_data[num_samples_to_waste : capture_param.num_samples_to_process + num_samples_to_waste]
            samples = dspmodule.dsp(samples, capture_param)

            wr_data = self.__serialize_capture_data(samples)
            addr = self.get_param(CaptureParamRegs.Offset.CAPTURE_ADDR) * 32
            self.__mem_writer(addr, wr_data)
            self.set_param(CaptureParamRegs.Offset.NUM_CAPTURED_SAMPLES, capture_param.calc_capture_samples())

            with self.__state_lock:
                if self.__state == CaptureUnitState.CAPTURE_WAVE:
                    self.__state = CaptureUnitState.COMPLETE
        except Exception as e:
            print('ERR [capture_wave] : {}'.format(e), file = sys.stderr)
            print('The e7awg_hw emulator has stopped!\n', file = sys.stderr)
            raise


    def __gen_capture_param(self):
        param = CaptureParam()
        # 積算区間数
        param.num_integ_sections = self.get_param(CaptureParamRegs.Offset.NUM_INTEG_SECTIONS)
        # 総和区間数
        num_sum_section = self.get_param(CaptureParamRegs.Offset.NUM_SUM_SECTIONS)
        # 総和区間長
        for i in range(num_sum_section):
            num_wave_words = self.get_param(CaptureParamRegs.Offset.sum_section_length(i))
            num_balnk_words = self.get_param(CaptureParamRegs.Offset.post_blank_length(i))
            param.add_sum_section(num_wave_words, num_balnk_words)
        # 有効 DSP モジュール
        dsp_units = self.get_param(CaptureParamRegs.Offset.DSP_MODULE_ENABLE)
        dsp_units = list(filter(lambda unit_id: (dsp_units >> unit_id) & 0x1, DspUnit.all()))
        param.sel_dsp_units_to_enable(*dsp_units)
        # キャプチャディレイ
        param.capture_delay = self.get_param(CaptureParamRegs.Offset.CAPTURE_DELAY)
        # 複素 FIR 係数
        param.complex_fir_coefs = [complex(
            self.__to_int32(self.get_param(CaptureParamRegs.Offset.comp_fir_re_coef(i))),
            self.__to_int32(self.get_param(CaptureParamRegs.Offset.comp_fir_im_coef(i))))
            for i in reversed(range(CaptureParam.NUM_COMPLEX_FIR_COEFS))]
        # 実 FIR 係数
        param.real_fir_i_coefs = [
            self.__to_int32(self.get_param(CaptureParamRegs.Offset.real_fir_i_coef(i)))
            for i in reversed(range(CaptureParam.NUM_REAL_FIR_COEFS))]
        param.real_fir_q_coefs = [
            self.__to_int32(self.get_param(CaptureParamRegs.Offset.real_fir_q_coef(i)))
            for i in reversed(range(CaptureParam.NUM_REAL_FIR_COEFS))]
        # 複素窓係数
        param.complex_window_coefs = [complex(
            self.__to_int32(self.get_param(CaptureParamRegs.Offset.comp_window_re_coef(i))),
            self.__to_int32(self.get_param(CaptureParamRegs.Offset.comp_window_im_coef(i))))
            for i in range(CaptureParam.NUM_COMPLEXW_WINDOW_COEFS)]
        # 総和開始ワード
        param.sum_start_word_no = self.get_param(CaptureParamRegs.Offset.SUM_START_TIME)
        # 総和ワード数
        sum_end_word_no = self.get_param(CaptureParamRegs.Offset.SUM_END_TIME)
        param.num_words_to_sum = sum_end_word_no - param.sum_start_word_no + 1
        return param


    def __calc_num_samples_to_waste(self, capture_delay):
        """キャプチャスタートから波形データの保存を開始するまでの間に捨てられるサンプル数を計算する"""
        num_samples = (self.__capture_start_delay + capture_delay + 1) * CaptureParam.NUM_SAMPLES_IN_ADC_WORD
        num_samples = (
            (num_samples + WaveSequence.NUM_SAMPLES_IN_WAVE_BLOCK - 1) // WaveSequence.NUM_SAMPLES_IN_WAVE_BLOCK)
        num_samples *= WaveSequence.NUM_SAMPLES_IN_WAVE_BLOCK
        return num_samples


    def __check_capture_size(self, param):
        """キャプチャデータ量が正常かどうか調べる"""
        dsp_units_enabled = param.dsp_units_enabled
        num_cap_samples = param.calc_capture_samples()
        try:
            # シミュレータの最大処理サンプル数のチェック
            if param.num_samples_to_process > self.__MAX_SAMPLES_IN_CAPTURE_SECTION:
                raise ValueError(
                    'No more than {} samples can be entered into the capture units in e7awg_hw emulator.\n  Tried to input {} samples.'
                    .format(self.__MAX_SAMPLES_IN_CAPTURE_SECTION + 1, param.num_samples_to_process))

            if DspUnit.INTEGRATION in dsp_units_enabled:
                # 積算ユニットが保持できる積算値の数をオーバーしていないかチェック
                if DspUnit.SUM in dsp_units_enabled:
                    # 総和が有効な場合, 積算の入力ワードの中に 1 サンプルしか含まれていないので, 
                    # 積算ベクトルの要素数 = 1 積算区間当たりのサンプル数となる
                    num_integ_vec_elems = num_cap_samples
                else:
                    num_integ_vec_elems = num_cap_samples // NUM_SAMPLES_IN_ADC_WORD

                if num_integ_vec_elems > MAX_INTEG_VEC_ELEMS:
                    raise ValueError(
                        "The number of elements in the capture unit {}'s integration result vector is too large.  (max = {}, setting = {})"
                        .format(self.__id, MAX_INTEG_VEC_ELEMS, num_integ_vec_elems))
            
            elif num_cap_samples > CaptureCtrl.MAX_CAPTURE_SAMPLES:
                raise ValueError(
                    'Capture unit {} has too many capture samples.  (max = {}, setting = {})'
                    .format(self.__id, CaptureCtrl.MAX_CAPTURE_SAMPLES, num_cap_samples))
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

        if DspUnit.SUM in dsp_units_enabled:
            for sum_sec_no in range(param.num_sum_sections):
                num_words_to_sum = self.__calc_num_words_in_sum_range(sum_sec_no, param)
                if num_words_to_sum > CaptureParam.MAX_SUM_RANGE_LEN:
                    msg = ('The size of the sum range in sum section {} on capture unit {} is too large.\n'
                           .format(sum_sec_no, self.__id))
                    msg += ('If the number of capture words to be summed exceeds {}, the sum may overflow.  {} was set.\n'
                            .format(CaptureParam.MAX_SUM_RANGE_LEN, num_words_to_sum))
                    log_warning(msg, *self.__loggers)
                    print('WARNING: ' + msg)


    def __calc_num_words_in_sum_range(self, sum_sec_no, param):
        num_words_in_sum_sec = param.sum_section(sum_sec_no)[0]
        if DspUnit.DECIMATION in param.dsp_units_enabled:
            num_words_in_sum_sec = ((num_words_in_sum_sec + 1) * CaptureParam.NUM_SAMPLES_IN_ADC_WORD) // 32

        sum_end_word_no = min(param.sum_start_word_no + param.num_words_to_sum - 1, num_words_in_sum_sec - 1)
        num_sum_words = sum_end_word_no - max(0, param.sum_start_word_no) + 1
        return max(num_sum_words, 0)


    def __serialize_capture_data(self, data):
        serialized = bytearray()
        for sample in data:
            serialized += struct.pack('<f', sample[0])
            serialized += struct.pack('<f', sample[1])
        return serialized
            

    def is_complete(self):
        """キャプチャユニットが complete 状態かどうか調べる"""
        return self.__state == CaptureUnitState.COMPLETE


    def is_busy(self):
        """キャプチャユニットが busy 状態かどうか調べる"""
        return self.__state == CaptureUnitState.CAPTURE_WAVE


    def is_wakeup(self):
        """キャプチャユニットが wakeup 状態かどうか調べる"""
        return self.__state != CaptureUnitState.RESET


    def set_param(self, addr, data):
        """キャプチャパラメータを設定する
        
        Args:
            addr (int): パラメータレジスタのアドレス
            data (int): 設定値
        """
        try:
            if addr % self.PARAM_REG_SIZE != 0:
                raise ValueError(
                    ('Capture parameter register address must be a multiple of {}.  ({}, AWG_{})'
                    .format(self.PARAM_REG_SIZE, addr, self.__id)))

            if (addr < 0) or (self.__MAX_PARAM_REG_ADDR < addr):
                raise ValueError(
                    'Capture parameter register address must be between 0x0 and 0x{:x} inclusive.  ({}, CaptureUnit_{})'
                    .format(self.__MAX_PARAM_REG_ADDR, addr, self.__id))

            if (data < 0) or (0xFFFFFFFF < data):
                raise ValueError(
                    'Capture parameter register value must be between 0 and {} inclusive.  ({}, CaptureUnit_{})'
                    .format(0xFFFFFFFF, data, self.__id))
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

        reg_idx = addr // self.PARAM_REG_SIZE
        self.__param_regs[reg_idx] = data


    def get_param(self, addr):
        """キャプチャパラメータを取得する
        
        Args:
            addr (int): パラメータレジスタのアドレス
        """
        try:
            if addr % self.PARAM_REG_SIZE != 0:
                raise ValueError(
                    ('Capture parameter register address must be a multiple of {}.  ({}, AWG_{})'
                    .format(self.PARAM_REG_SIZE, addr, self.__id)))

            if (addr < 0) or (self.__MAX_PARAM_REG_ADDR < addr):
                raise ValueError(
                    'Capture parameter register address must be between 0x0 and 0x{:x} inclusive.  ({}, CaptureUnit_{})'
                    .format(self.__MAX_PARAM_REG_ADDR, addr, self.__id))
        except Exception as e:
            log_error(e, *self.__loggers)
            raise
        
        reg_idx = addr // self.PARAM_REG_SIZE
        return self.__param_regs[reg_idx]


    def __set_default_params(self):
        self.set_param(CaptureParamRegs.Offset.NUM_INTEG_SECTIONS, 1)
        self.set_param(CaptureParamRegs.Offset.NUM_SUM_SECTIONS, 1)
        for i in range(CaptureParam.MAX_SUM_SECTIONS):
            sum_sec_addr = CaptureParamRegs.Offset.sum_section_length(i)
            post_blank_addr = CaptureParamRegs.Offset.post_blank_length(i)
            self.set_param(sum_sec_addr, 1)
            self.set_param(post_blank_addr, 1)


    def __to_int32(self, val):
        val = val & 0xffffffff
        return (val ^ 0x80000000) - 0x80000000


class CaptureUnitState(IntEnum):
    RESET = 0
    IDLE  = 1
    CAPTURE_WAVE = 3
    COMPLETE = 4
