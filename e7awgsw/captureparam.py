from .hwparam import *
from .hwdefs import *
import copy
from .logger import *

class CaptureParam(object):
    """ キャプチャパラメータを保持するクラス"""

    MAX_INTEG_SECTIONS = 1048576           #: 最大統合区間数
    MAX_SUM_SECTIONS = MAX_INTEG_VEC_ELEMS #: 1統合区間当たりの最大総和区間数
    NUM_COMPLEX_FIR_COEFS = 16             #: 複素 FIR フィルタの係数の数
    NUM_REAL_FIR_COEFS = 8                 #: 実数 FIR フィルタの係数の数
    NUM_COMPLEXW_WINDOW_COEFS = 2048       #: 複素窓関数の係数の数

    MIN_FIR_COEF_VAL = -32768          #: 複素 or 実数 FIR フィルタの係数の最小値
    MAX_FIR_COEF_VAL = 32767           #: 複素 or 実数 FIR フィルタの係数の最大値
    MIN_WINDOW_COEF_VAL = -2147483648  #: 窓関数の係数の最小値
    MAX_WINDOW_COEF_VAL = 2147483647   #: 窓関数の係数の最大値
    MAX_CAPTURE_DELAY = 0xFFFFFFFE     #: キャプチャディレイの最大値

    MAX_SUM_SECTION_LEN = 0xFFFFFFFE   #: 最大総和区間長
    MAX_POST_BLANK_LEN = 0xFFFFFFFF    #: 最大ポストブランク長

    MAX_SUM_RANGE_LEN = 1024           #: オーバーフローせずに総和可能な総和範囲の長さ (単位：キャプチャワード)
    
    NUM_SAMPLES_IN_ADC_WORD = NUM_SAMPLES_IN_ADC_WORD #: 1 キャプチャワード当たりのサンプル数

    def __init__(self, *, enable_lib_log = True, logger = get_null_logger()):
        """
        Args:
            enable_lib_log (bool):
                | True -> ライブラリの標準のログ機能を有効にする.
                | False -> ライブラリの標準のログ機能を無効にする.
            logger (logging.Logger): ユーザ独自のログ出力に用いる Logger オブジェクト
        """
        self.__num_integ_sections = 1
        self.__sumsections = []
        self.__dsp_units = []
        self.__capture_delay = 0
        self.__comp_fir_coefs = [0 + 0j] * self.NUM_COMPLEX_FIR_COEFS
        self.__real_fir_i_coefs = [0] * self.NUM_REAL_FIR_COEFS
        self.__real_fir_q_coefs = [0] * self.NUM_REAL_FIR_COEFS
        self.__comp_window_coefs = [0 + 0j] * self.NUM_COMPLEXW_WINDOW_COEFS
        self.__sum_start_word_no = 0
        self.__num_words_to_sum = self.MAX_SUM_SECTION_LEN
        self.__loggers = [logger]
        if enable_lib_log:
            self.__loggers.append(get_file_logger())

    @property
    def num_integ_sections(self):
        """積算区間数
        
        Args:
            val (int): 積算区間数
        Returns:
            int: 積算区間数
        """
        return self.__num_integ_sections

    @num_integ_sections.setter
    def num_integ_sections(self, val):
        if not (isinstance(val, int) and (1 <= val and val <= self.MAX_INTEG_SECTIONS)):
            msg = ("The number of integration sections must be an integer between {} and {} inclusive.  '{}' was set."
                  .format(1, self.MAX_INTEG_SECTIONS, val))
            log_error(msg, *self.__loggers)
            raise ValueError(msg)
        
        self.__num_integ_sections = val

    def add_sum_section(self, num_words, num_post_blank_words):
        """総和区間を追加する

        Args:
            num_words (int): 
                | 追加する総和区間の長さ. (単位: キャプチャワード)
                | 1 キャプチャワード = 4 サンプル (I データと Q データはまとめて 1 サンプルとカウントする.)
            num_post_blank_words (int):
                | 追加する総和区間に続くポストブランクの長さ. (単位: キャプチャワード)
                | ポストブランクの間のサンプルデータはキャプチャ対象にならない.
                | 1 以上を指定すること.
        """
        try:
            if (len(self.__sumsections) == self.MAX_SUM_SECTIONS):
                raise ValueError("No more sum sections can be added. (max=" + str(self.MAX_SUM_SECTIONS) + ")")

            if not (isinstance(num_words, int) and 
                    (1 <= num_words and num_words <= self.MAX_SUM_SECTION_LEN)):
                raise ValueError(
                    "Sum sections length must be an integer between {} and {} inclusive.  '{}' was set."
                    .format(1, self.MAX_SUM_SECTION_LEN, num_words))

            if not (isinstance(num_post_blank_words, int) and 
                    (1 <= num_post_blank_words and num_post_blank_words <= self.MAX_POST_BLANK_LEN)):
                raise ValueError(
                    "Post blank length must be an integer between {} and {} inclusive.  '{}' was set."
                    .format(1, self.MAX_POST_BLANK_LEN, num_post_blank_words))
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

        self.__sumsections.append((num_words, num_post_blank_words))

    @property
    def num_sum_sections(self):
        """総和区間数
        
        Returns:
            int: 現在登録されている総和区間の数
        """
        return len(self.__sumsections)

    def sum_section(self, idx):
        """引数で指定した総和区間のパラメータを取得する

        Args:
            idx (int): パラメータを取得する総和区間のインデックス

        Returns:
            (int, int): (総和区間長, ポストブランク長)  (単位: キャプチャワード)
        """
        return self.__sumsections[idx]

    @property
    def sum_section_list(self):
        """登録されている全総和区間とポストブランクの長さのリスト

        Returns:
            list of (int, int): 総和区間長 と ポストブランク長のタプルのリスト
        """
        return copy.copy(self.__sumsections)

    @property
    def num_samples_to_process(self): 
        """処理対象となる ADC データのサンプル数 (I データと Q データはまとめて 1 サンプルとカウント)

        Returns:
            int: 
                | 処理対象となる ADC データのサンプル数.
                | ポストブランクの間のサンプルも含む.
        """
        num_samples = 0
        for sum_section in self.__sumsections:
            num_samples += (sum_section[0] + sum_section[1]) * NUM_SAMPLES_IN_ADC_WORD
        return num_samples * self.__num_integ_sections

    def sel_dsp_units_to_enable(self, *dsp_units):
        """このキャプチャシーケンスで有効にする信号処理ユニットを選択する.

        引数に含まなかった信号処理ユニットは無効になる.
        
        Args:
            *dsp_units (DspUnit): 有効にする DSP ユニットの ID
        """
        if not DspUnit.includes(*dsp_units):
            msg = 'Invalid DSP Unit  {}'.format(dsp_units)
            log_error(msg, *self.__loggers)
            raise ValueError(msg)
        self.__dsp_units = dsp_units

    @property
    def dsp_units_enabled(self):
        """現在有効になっている DSP ユニットのリスト

        Returns:
            list of DspUnit: 現在有効になっている DSP ユニットのリスト
        """
        return list(self.__dsp_units)

    @property
    def capture_delay(self):
        """キャプチャディレイ

        | 単位はキャプチャワード.
        | 1 キャプチャワードは 4 サンプル. (I データと Q データはまとめて 1 サンプルとカウント)
        | 
        | キャプチャユニットは以下の順番で受信波形のキャプチャを開始する
        | 1. キャプチャ開始トリガを受信する
        | 2. キャプチャディレイが経過するのを待つ
        | 3. 受信波形のブロック (1 ブロックは 64 サンプル) の先頭データが来るのを待つ
        | 4. 受信波形のブロックの先頭データからキャプチャを開始する

        Args:
            val (int): キャプチャディレイ値

        Returns:
            int: 現在設定されているキャプチャディレイ
        """
        return self.__capture_delay

    @capture_delay.setter
    def capture_delay(self, val):
        if not (isinstance(val, int) and (0 <= val and val <= self.MAX_CAPTURE_DELAY)):
            msg = ("Capture Delay must be an integer between {} and {} inclusive.  '{}' was set."
                    .format(0, self.MAX_CAPTURE_DELAY, val))
            log_error(msg, *self.__loggers)
            raise ValueError(msg)
        self.__capture_delay = val

    @property
    def complex_fir_coefs(self):
        """複素 FIR フィルタの係数のリスト

        Args:
            val (list of [complex | float | int]):
                | 複素係数のリスト. 
                | 各係数の実数および虚数成分は整数値とすること.
                | 指定しなかった分の係数は全て 0 + 0j となる.
        Returns:
            list of complex: 複素 FIR フィルタの係数のリスト
        """
        return copy.copy(self.__comp_fir_coefs)

    @complex_fir_coefs.setter
    def complex_fir_coefs(self, val):
        try:
            if not isinstance(val, list):
                raise ValueError('Invalid coefficient list  ({})'.format(val))

            num_coefs = len(val)
            if num_coefs == 0:
                raise ValueError('Empty coefficient list was set.')

            if num_coefs > self.NUM_COMPLEX_FIR_COEFS:
                raise ValueError(
                    'Complex FIR filter has up to {} coefficients.  {} coefficients were set.'
                    .format(self.NUM_COMPLEX_FIR_COEFS, num_coefs))
            
            if not all([isinstance(coef, (float, int, complex)) for coef in val]):
                raise ValueError("The type of complex FIR coefficients must be 'complex', 'float' or 'int'.")

            val = [complex(coef) for coef in val] + [0 + 0j] * (self.NUM_COMPLEX_FIR_COEFS - num_coefs)
            if not all([coef.real.is_integer() and coef.imag.is_integer() for coef in val]):
                raise ValueError('Each part of a complex FIR coefficient must be an integer.')

            if not all([self.__is_in_range(self.MIN_FIR_COEF_VAL, self.MAX_FIR_COEF_VAL, coef.real) and 
                        self.__is_in_range(self.MIN_FIR_COEF_VAL, self.MAX_FIR_COEF_VAL, coef.imag)
                        for coef in val]):
                raise ValueError('Each part of a complex FIR coefficient must be {} ~ {}.'
                    .format(self.MIN_FIR_COEF_VAL, self.MAX_FIR_COEF_VAL))
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

        self.__comp_fir_coefs = val

    @property
    def real_fir_i_coefs(self):
        """I データ用実数 FIR フィルタの係数
        
        Args:
            val (list of [float | int]):
                | 係数のリスト.
                | 各係数は整数値とすること.
                | 指定しなかった分の係数は全て 0 となる.
        Returns:
            list of int: I データ用実数 FIR フィルタの係数リスト
        """
        return copy.copy(self.__real_fir_i_coefs)

    @real_fir_i_coefs.setter
    def real_fir_i_coefs(self, val):
        self.__check_real_fir_coef_set(val)
        self.__real_fir_i_coefs = [int(coef) for coef in val] + [0] * (self.NUM_REAL_FIR_COEFS - len(val))

    @property
    def real_fir_q_coefs(self):
        """Q データ用実数 FIR フィルタの係数を設定する.
        
        Args:
            val (list of [float | int]):
                | 係数のリスト.
                | 各係数は整数値とすること.
                | 指定しなかった分の係数は全て 0 となる.
        Returns:
            list of int: Q データ用実数 FIR フィルタの係数リスト
        """
        return copy.copy(self.__real_fir_q_coefs)

    @real_fir_q_coefs.setter
    def real_fir_q_coefs(self, val):
        self.__check_real_fir_coef_set(val)
        self.__real_fir_q_coefs = [int(coef) for coef in val] + [0] * (self.NUM_REAL_FIR_COEFS - len(val))

    def __check_real_fir_coef_set(self, val):
        """実数 FIR の係数が正常かどうかチェック"""
        try:
            if not isinstance(val, list):
                raise ValueError('Invalid coefficient list  ({})'.format(val))
            
            num_coefs = len(val)
            if num_coefs == 0:
                raise ValueError('Empty coefficient list was set.')

            if num_coefs > self.NUM_REAL_FIR_COEFS:
                raise ValueError(
                    'Real FIR filter has up to {} coefficients.  {} coefficients were set.'
                    .format(self.NUM_REAL_FIR_COEFS, num_coefs))
            
            if not all([isinstance(coef, (int, float)) for coef in val]):
                raise ValueError("The type of real FIR coefficients must be 'int' or 'float'.")

            if not all([float(coef).is_integer() for coef in val]):
                raise ValueError('Real FIR coefficients must be an integer.')

            if not all([self.__is_in_range(self.MIN_FIR_COEF_VAL, self.MAX_FIR_COEF_VAL, coef) for coef in val]):
                raise ValueError('Real FIR coefficients must be {} ~ {}.'
                    .format(self.MIN_FIR_COEF_VAL, self.MAX_FIR_COEF_VAL))
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

    @property
    def complex_window_coefs(self):
        """複素窓関数の係数リスト

        Args:
            val (list of [complex | floar | int]):
                | 複素係数のリスト. 
                | 各係数の実数および虚数成分は整数値とすること.
                | 指定しなかった分の係数は全て 0 + 0j となる.
        Returns:
            list of complex: 複素窓関数の係数リスト
        """
        return copy.copy(self.__comp_window_coefs)

    @complex_window_coefs.setter
    def complex_window_coefs(self, val):
        try:
            if not isinstance(val, list):
                raise ValueError('Invalid coefficient list  ({})'.format(val))

            num_coefs = len(val)
            if num_coefs == 0:
                raise ValueError('Empty coefficient list was set.')

            if num_coefs > self.NUM_COMPLEXW_WINDOW_COEFS:
                raise ValueError(
                    'Complex window has up to {} coefficients.  {} coefficients were set.'
                    .format(self.NUM_COMPLEXW_WINDOW_COEFS, num_coefs))
            
            if not all([isinstance(coef, (float, int, complex)) for coef in val]):
                raise ValueError("The type of complex window coefficients must be 'complex', 'float' or 'int'.")

            val = [complex(coef) for coef in val] + [0 + 0j] * (self.NUM_COMPLEXW_WINDOW_COEFS - num_coefs)
            if not all([coef.real.is_integer() and coef.imag.is_integer() for coef in val]):
                raise ValueError('Each part of a complex window coefficient must be an integer.')

            if not all([self.__is_in_range(self.MIN_WINDOW_COEF_VAL, self.MAX_WINDOW_COEF_VAL, coef.real) and 
                        self.__is_in_range(self.MIN_WINDOW_COEF_VAL, self.MAX_WINDOW_COEF_VAL, coef.imag)
                        for coef in val]):
                raise ValueError(
                    'Each part of a complex window coefficient must be {} ~ {}.'
                    .format(self.MIN_WINDOW_COEF_VAL, self.MAX_WINDOW_COEF_VAL))
        except Exception as e:
            log_error(e, *self.__loggers)
            raise

        self.__comp_window_coefs = val
    
    def calc_capture_samples(self):
        """現在のキャプチャパラメータで保存されるサンプル数を計算する

        Returns:
            現在のキャプチャパラメータで保存されるサンプル数
        """
        num_samples_in_integ_section = 0
        dsp_units_enabled = self.dsp_units_enabled
        for i in range(self.num_sum_sections):
            num_cap_words = self.__sumsections[i][0]
            if DspUnit.SUM in dsp_units_enabled:
                # 総和が有効だと総和区間のサンプルは 1 つにまとめられる
                num_samples_in_integ_section += 1
            elif DspUnit.DECIMATION in dsp_units_enabled:
                # 間引きは 8 で割った余りが 7 のとき, 出力ワード数が切り上げになる. 
                # つまり, 7 ワード入力すると 1 ワード出力され, 15 ワード入力すると 2 ワード出力される.
                num_samples_in_integ_section += ((num_cap_words + 1) // 8) * NUM_SAMPLES_IN_ADC_WORD
            else:
                num_samples_in_integ_section += num_cap_words * NUM_SAMPLES_IN_ADC_WORD
                
        if DspUnit.INTEGRATION in dsp_units_enabled:
            return num_samples_in_integ_section

        return num_samples_in_integ_section * self.__num_integ_sections

    @property
    def sum_start_word_no(self):
        """総和を開始するキャプチャワードの番号

            | 総和区間の N 番目のキャプチャワードをキャプチャワード N (≧0) としたとき,
            | N が以下の条件を満たすキャプチャワード N が総和対象となる.
            | 
            | 総和開始点 = sum_start_word_no (≧ 0)
            | 総和終了点 = sum_start_word_no + num_words_to_sum - 1 (≦ 4294967294)
            | 総和開始点 ≦ N ≦ 総和終了点

        Args:
            val (int):
                | 各総和区間内で総和を開始するキャプチャワードの番号. (≧ 0)
                | 間引きが有効になっている場合, 間引き後に残ったキャプチャワードのみ数える.
                | (総和区間のキャプチャワード数 - 1) < sum_start_word_no の場合, その総和区間の総和は算出されない.
        Returns:
            int: 総和を開始するキャプチャワードの番号
        """
        return self.__sum_start_word_no

    @sum_start_word_no.setter
    def sum_start_word_no(self, val):
        if not (isinstance(val, int) and 
                (0 <= val and val <= self.MAX_SUM_SECTION_LEN)):
            msg = ("Sum start word number must be an integer between {} and {} inclusive.  '{}' was set."
                .format(0, self.MAX_SUM_SECTION_LEN, val))
            log_error(msg, *self.__loggers)
            raise ValueError(msg)
        self.__sum_start_word_no = val

    @property
    def num_words_to_sum(self):
        """総和するキャプチャワード数

            | 総和区間の N 番目のキャプチャワードをキャプチャワード N (≧0) としたとき,
            | N が以下の条件を満たすキャプチャワード N が総和対象となる.
            | 
            | 総和開始点 = sum_start_word_no (≧ 0)
            | 総和終了点 = sum_start_word_no + num_words_to_sum - 1 (≦ 4294967294)
            | 総和開始点 ≦ N ≦ 総和終了点

        Args:
            val (int):
                | 各総和区間内で総和対象とするキャプチャワードの数.
                | 間引きが有効になっている場合, 間引き後に残ったキャプチャワードのみ数える.
        Returns:
            int: 総和するキャプチャワード数
        """
        return self.__num_words_to_sum

    @num_words_to_sum.setter
    def num_words_to_sum(self, val):
        if not (isinstance(val, int) and (1 <= val)):
            msg = ("The number of capture words to be added up must be greater than or equal to 1.  '{}' was set."
                .format(val))
            log_error(msg, *self.__loggers)
            raise ValueError(msg)
        self.__num_words_to_sum = val

    def __is_in_range(self, min, max, val):
        return (min <= val) and (val <= max)

    def __str__(self):
        retstr = []
        retstr.append('num integration sections : {}\n'.format(self.__num_integ_sections))
        retstr.append('num sum sections : {}\n'.format(self.num_sum_sections))
        retstr.append('capture delay : {}\n'.format(self.capture_delay))
        retstr.append('sum start word no : {}\n'.format(self.sum_start_word_no))
        retstr.append('num words to sum : {}\n\n'.format(self.num_words_to_sum))
        retstr.append('num samples to be processed : {}\n'.format(self.num_samples_to_process))
        retstr.append('num samples to be captured : {}\n\n'.format(self.calc_capture_samples()))
        
        retstr.append('sum sections\n')
        for i in range(self.num_sum_sections):
            cap_len = self.sum_section(i)[0]
            blank_len = self.sum_section(i)[1]
            retstr.append('    section {}\n'.format(i))
            retstr.append('        num capture words : {}   ({})\n'.format(cap_len, cap_len * NUM_SAMPLES_IN_ADC_WORD))
            retstr.append('        num blank words : {}   ({})\n'.format(blank_len, blank_len * NUM_SAMPLES_IN_ADC_WORD))
        
        retstr.append('\nDSP units enabled\n')
        for dsp_unit in self.dsp_units_enabled:
            retstr.append('    {}\n'.format(dsp_unit))
        
        retstr.append('\ncomplex fir coefficients\n')
        for i in range(len(self.__comp_fir_coefs)):
            retstr.append('    {:2d} : {}\n'.format(i, self.__comp_fir_coefs[i]))

        retstr.append('\nreal I fir coefficients\n')
        for i in range(len(self.__real_fir_i_coefs)):
            retstr.append('    {} : {}\n'.format(i, self.__real_fir_i_coefs[i]))

        retstr.append('\nreal Q fir coefficients\n')
        for i in range(len(self.__real_fir_q_coefs)):
            retstr.append('    {} : {}\n'.format(i, self.__real_fir_q_coefs[i]))

        retstr.append('\ncomplex window coefficients\n')
        for i in range(len(self.__comp_window_coefs)):
            retstr.append('    {} : {}\n'.format(i, self.__comp_window_coefs[i]))

        return ''.join(retstr)
